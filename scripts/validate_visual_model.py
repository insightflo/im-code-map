#!/usr/bin/env python3
"""Validate visual-model v5 profile semantics and traceability to the shared evidence model."""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

from im_code_map_common import ensure_unique_ids, read_json


def schema_errors(data: dict[str, Any], schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except Exception:
        return ["jsonschema is not installed; structural schema validation skipped"]
    schema = read_json(schema_path)
    return [f"schema {'.'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.absolute_path))]


def validate(data: dict[str, Any], map_model: dict[str, Any] | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    diagrams = data.get("diagrams", [])
    profile = data.get("profile")
    if profile not in {"focus", "atlas"}:
        errors.append("visual-model profile must be focus or atlas")
    policy = data.get("reader_policy", {})
    if profile == "focus":
        if policy.get("detail_policy") != "progressive-disclosure":
            errors.append("Focus visual-model must use progressive-disclosure")
        if policy.get("implementation_identifiers") == "visible":
            errors.append("Focus visual-model must not expose implementation identifiers in first-view cards")
    if profile == "atlas" and policy.get("detail_policy") != "full-detail":
        warnings.append("Atlas visual-model normally uses full-detail reader policy")
    duplicates = ensure_unique_ids(diagrams, "diagram")
    if duplicates:
        errors.append(f"duplicate diagram ids: {duplicates}")
    diagram_ids = {d["id"] for d in diagrams}
    max_words = int(data.get("style_profile", {}).get("max_card_words", 28))
    max_nodes = int(data.get("style_profile", {}).get("max_nodes_per_frame", 18))

    for diagram in diagrams:
        did = diagram["id"]
        if diagram.get("profile") != profile:
            errors.append(f"diagram {did} profile does not match root profile {profile}")
        frame_ids = {f["id"] for f in diagram.get("frames", [])}
        lane_ids = {l["id"] for l in diagram.get("lanes", [])}
        node_dupes = ensure_unique_ids(diagram.get("nodes", []), f"diagram {did} node")
        edge_dupes = ensure_unique_ids(diagram.get("edges", []), f"diagram {did} edge")
        if node_dupes:
            errors.append(f"diagram {did} duplicate nodes: {node_dupes}")
        if edge_dupes:
            errors.append(f"diagram {did} duplicate edges: {edge_dupes}")
        nodes = {n["id"]: n for n in diagram.get("nodes", [])}
        contract = diagram.get("reader_contract", {})
        if contract.get("start_here_node_id") not in nodes:
            errors.append(f"diagram {did} reader_contract start_here_node_id references unknown node")
        contract_primary = contract.get("primary_story_node_ids", [])
        missing_contract_nodes = [x for x in contract_primary if x not in nodes]
        if missing_contract_nodes:
            errors.append(f"diagram {did} reader_contract references unknown primary nodes: {missing_contract_nodes}")
        if not contract.get("does_not_answer"):
            errors.append(f"diagram {did} reader_contract must state what the diagram does not answer")
        outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
        incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
        frame_counts: dict[str, int] = defaultdict(int)
        layout_slots: dict[tuple[Any, Any, Any], list[str]] = defaultdict(list)
        for node in nodes.values():
            if node.get("frame") not in frame_ids:
                errors.append(f"diagram {did} node {node['id']} references unknown frame")
            if node.get("lane") not in lane_ids:
                errors.append(f"diagram {did} node {node['id']} references unknown lane")
            frame_counts[node.get("frame")] += 1
            layout_slots[(node.get("frame"), node.get("lane"), node.get("order"))].append(node["id"])
            if len(str(node.get("summary", "")).split()) > max_words:
                errors.append(f"diagram {did} node {node['id']} summary exceeds max_card_words={max_words}")
            if node.get("kind") in {"process", "decision", "state-change", "error", "compensation", "domain"} and not node.get("details_link"):
                warnings.append(f"diagram {did} node {node['id']} has no details_link")
            if node.get("kind") == "state-change" and not (node.get("state_before") and node.get("state_after")):
                warnings.append(f"diagram {did} state-change {node['id']} does not show before/after state")
        for fid, count in frame_counts.items():
            if count > max_nodes:
                errors.append(f"diagram {did} frame {fid} has {count} nodes; max is {max_nodes}; split into phases or child diagrams")
        for (frame_id, lane_id, order), node_ids in layout_slots.items():
            if len(node_ids) > 1:
                errors.append(
                    f"diagram {did} nodes {node_ids} share layout slot "
                    f"frame={frame_id} lane={lane_id} order={order}; split outcomes or assign distinct orders"
                )

        for edge in diagram.get("edges", []):
            if edge.get("from") not in nodes or edge.get("to") not in nodes:
                errors.append(f"diagram {did} edge {edge['id']} references unknown node")
                continue
            outgoing[edge["from"]].append(edge)
            incoming[edge["to"]].append(edge)
            if edge.get("kind") in {"conditional", "error", "retry", "timeout", "compensation", "cancel"} and not edge.get("condition"):
                errors.append(f"diagram {did} edge {edge['id']} needs condition text")
        if diagram.get("type") == "business-stream":
            starts = [n for n in nodes.values() if n.get("kind") == "start"]
            ends = [n for n in nodes.values() if n.get("kind") == "end"]
            if not starts:
                errors.append(f"business-stream diagram {did} has no start")
            if not ends:
                errors.append(f"business-stream diagram {did} has no end")
            for node in nodes.values():
                if node.get("kind") == "decision":
                    branches = outgoing.get(node["id"], [])
                    if len(branches) < 2:
                        errors.append(f"diagram {did} decision {node['id']} has fewer than two branches")
                    for branch in branches:
                        if not branch.get("condition"):
                            errors.append(f"diagram {did} decision branch {branch['id']} lacks condition")
                if node.get("kind") == "end" and outgoing.get(node["id"]):
                    errors.append(f"diagram {did} end node {node['id']} has outgoing edge")
                if node.get("kind") == "start" and incoming.get(node["id"]):
                    warnings.append(f"diagram {did} start node {node['id']} has incoming edge")
            if diagram.get("layout", {}).get("lane_axis") != "actor-system":
                warnings.append(f"business-stream diagram {did} is not actor-system lane based")
        if diagram.get("type") == "focus-flow":
            starts = [n for n in nodes.values() if n.get("kind") == "start"]
            ends = [n for n in nodes.values() if n.get("kind") == "end"]
            if not starts or not ends:
                errors.append(f"focus-flow diagram {did} must expose a start and success end")
            decisions = [n for n in nodes.values() if n.get("kind") == "decision" and n.get("role") == "decision"]
            if len(decisions) > 4:
                errors.append(f"focus-flow diagram {did} exposes more than four decisions")
            if not any(n.get("role") == "failure-summary" for n in nodes.values()):
                errors.append(f"focus-flow diagram {did} has no failure summary")
            if not any(n.get("role") == "atlas-link" for n in nodes.values()):
                errors.append(f"focus-flow diagram {did} has no Atlas progression link")
        if diagram.get("type") == "human-overview" and len(contract_primary) > 6:
            errors.append(f"human-overview {did} has more than six first-view nodes")
        if diagram.get("type") == "domain-overview" and any(n.get("kind") == "start" for n in nodes.values()):
            warnings.append(f"domain-overview {did} contains start nodes; verify it is not secretly a business stream")
        if not diagram.get("navigation", {}).get("related_notes"):
            warnings.append(f"diagram {did} has no related note links")

    for composition in data.get("compositions", []):
        if composition.get("mode") == "merge-elements" and len(composition.get("placements", [])) < 2:
            errors.append(f"composition {composition['id']} must combine at least two diagrams")
        for placement in composition.get("placements", []):
            if placement.get("diagram_id") not in diagram_ids:
                errors.append(f"composition {composition['id']} references unknown diagram {placement.get('diagram_id')}")

    if map_model:
        stream_ids = {s["id"] for s in map_model.get("business_streams", [])}
        visualized = set()
        accepted_types = {"business-stream"} if profile == "atlas" else {"focus-flow"}
        for diagram in diagrams:
            if diagram.get("type") in accepted_types:
                visualized.update(set(diagram.get("source_refs", [])) & stream_ids)
        if profile == "atlas":
            missing = stream_ids - visualized
            if missing:
                errors.append(f"business streams without Atlas business-stream diagram: {sorted(missing)}")
            domain_ids = {d["id"] for d in map_model.get("domains", [])}
            domain_refs = set().union(*(set(d.get("source_refs", [])) for d in diagrams if d.get("type") == "domain-overview")) if diagrams else set()
            missing_domains = domain_ids - domain_refs
            if missing_domains:
                warnings.append(f"domains absent from Atlas overview source_refs: {sorted(missing_domains)}")
        elif not visualized:
            errors.append("Focus visual-model does not trace any map-model business stream")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visual_model", type=Path)
    parser.add_argument("--map-model", type=Path)
    parser.add_argument("--schema", type=Path, default=None)
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()
    data = read_json(args.visual_model)
    schema = args.schema or Path(__file__).resolve().parents[1] / "templates" / "visual-model.schema.json"
    s_errors = schema_errors(data, schema)
    warnings = [x for x in s_errors if x.startswith("jsonschema")]
    errors = [x for x in s_errors if not x.startswith("jsonschema")]
    semantic_errors, semantic_warnings = validate(data, read_json(args.map_model) if args.map_model else None)
    errors.extend(semantic_errors); warnings.extend(semantic_warnings)
    for message in warnings:
        print(f"WARN: {message}")
    for message in errors:
        print(f"FAIL: {message}")
    if not errors:
        print(f"PASS: visual-model schema, stream semantics, and composition references ({len(data.get('diagrams', []))} diagrams)")
    print(f"SUMMARY errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors or (args.strict_warnings and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
