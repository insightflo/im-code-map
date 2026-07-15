#!/usr/bin/env python3
"""Generate a stream-first JSON Canvas navigation map."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from im_code_map_common import read_json, stable_id, write_json


def node(kind: str, key: str, x: int, y: int, w: int, h: int, **extra: Any) -> dict[str, Any]:
    return {"id": stable_id("canvas", key), "type": kind, "x": x, "y": y, "width": w, "height": h, **extra}


def edge(key: str, fr: str, to: str, label: str = "", from_side: str = "right", to_side: str = "left") -> dict[str, Any]:
    e = {"id": stable_id("edge", key), "fromNode": fr, "toNode": to, "fromSide": from_side, "toSide": to_side}
    if label:
        e["label"] = label
    return e


def generate(model: dict[str, Any], visual: dict[str, Any], prefix: str) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []; edges: list[dict[str, Any]] = []
    streams = model.get("business_streams", []); domains = model.get("domains", [])
    states = model.get("state_machines", []); entities = model.get("entities", [])
    codebases = model.get("codebases", []); rules = model.get("business_rules", [])
    diagrams = list(visual.get("diagrams", []))

    start = node("file", "start-here", 40, 40, 360, 220, file=f"{prefix}/start-here.md")
    visual_index = node("file", "visual-index", 450, 40, 340, 220, file=f"{prefix}/visual-index.md")
    nodes.extend([start, visual_index]); edges.append(edge("start-visual", start["id"], visual_index["id"], "visual entry"))

    group_stream = node("group", "group-streams", 20, 330, 1780, max(760, 330 + len(streams)*330), label="1. Business streams: begin here")
    group_state = node("group", "group-state", 1870, 330, 1420, max(760, 250 + (len(states)+len(rules))*210), label="2. State, eligibility, and rules")
    group_domain = node("group", "group-domain", 3360, 330, 1500, max(760, 240 + len(domains)*190), label="3. Domain ownership and contracts")
    group_code = node("group", "group-code", 4930, 330, 1250, max(760, 250 + len(codebases)*220), label="4. Codebases and evidence")
    nodes.extend([group_stream, group_state, group_domain, group_code])

    stream_nodes: dict[str, str] = {}; domain_nodes: dict[str, str] = {}; state_nodes: dict[str, str] = {}; rule_nodes: dict[str, str] = {}
    for i, stream in enumerate(streams):
        y = 400 + i*330
        note = node("file", f"stream-note:{stream['id']}", 80, y, 440, 210, file=f"{prefix}/flows/{stream['id']}.md")
        # The map-model may list both Focus and Atlas drawing paths.  This Canvas is
        # generated from an Atlas visual model, so resolve the child by visual source_ref
        # instead of blindly taking diagram_paths[0] and re-prefixing it under /atlas.
        visual_diagram = next((
            item for item in diagrams
            if item.get("type") == "business-stream" and stream["id"] in item.get("source_refs", [])
        ), None)
        if visual_diagram:
            diag_name = f"{visual_diagram['id']}.excalidraw"
        else:
            candidates = [Path(path).name for path in stream.get("diagram_paths", []) if "/atlas/" in str(path).replace("\\", "/")]
            diag_name = candidates[0] if candidates else f"stream-{stream['id']}.excalidraw"
        diag = node("file", f"stream-diagram:{stream['id']}", 570, y, 500, 210, file=f"{prefix}/excalidraw/{diag_name}")
        summary = node("text", f"stream-summary:{stream['id']}", 1120, y, 590, 210,
                       text=f"**Trigger**: {stream['trigger']['event']}\n\n**Entry**: `{stream['trigger']['entry_point']}`\n\n**Terminal outcomes**: {len(stream.get('outcomes', []))}\n\n**Confidence**: `{stream['confidence']}`")
        nodes.extend([note, diag, summary]); stream_nodes[stream["id"]] = note["id"]
        edges.extend([edge(f"stream-diag:{stream['id']}", note["id"], diag["id"], "visual"), edge(f"stream-summary:{stream['id']}", diag["id"], summary["id"], "trigger / result")])
        if i == 0: edges.append(edge("start-primary-stream", start["id"], note["id"], "start reading", "bottom", "top"))

    sy = 400
    for i, machine in enumerate(states):
        n = node("file", f"state:{machine['id']}", 1930, sy+i*210, 420, 170, file=f"{prefix}/states/{machine['id']}.md")
        nodes.append(n); state_nodes[machine["id"]] = n["id"]
    rule_y = sy + len(states)*210 + 40
    for i, rule in enumerate(rules):
        n = node("file", f"rule:{rule['id']}", 2410, rule_y+i*190, 780, 150, file=f"{prefix}/rules/{rule['id']}.md")
        nodes.append(n); rule_nodes[rule["id"]] = n["id"]
        for sid in rule.get("used_by_streams", []):
            if sid in stream_nodes:
                edges.append(edge(f"rule-stream:{rule['id']}:{sid}", stream_nodes[sid], n["id"], "evaluates", "right", "left"))

    for i, domain in enumerate(domains):
        x = 3420 + (i%2)*700; y = 400 + (i//2)*190
        n = node("file", f"domain:{domain['id']}", x, y, 620, 150, file=f"{prefix}/domains/{domain['id']}.md")
        nodes.append(n); domain_nodes[domain["id"]] = n["id"]
        for sid in domain.get("participating_streams", []):
            if sid in stream_nodes:
                edges.append(edge(f"stream-domain:{sid}:{domain['id']}", stream_nodes[sid], n["id"], "uses", "right", "left"))

    for i, cb in enumerate(codebases):
        n = node("file", f"codebase:{cb['id']}", 5000, 400+i*220, 540, 180, file=f"{prefix}/codebases/{cb['id']}.md")
        nodes.append(n)
        evidence = node("text", f"codebase-evidence:{cb['id']}", 5580, 400+i*220, 520, 180,
                        text=f"**Root** `{cb['root_path']}`\n\n**Entry points**\n" + "\n".join(f"- `{p}`" for p in cb.get("entry_points", [])))
        nodes.append(evidence); edges.append(edge(f"cb-evidence:{cb['id']}", n["id"], evidence["id"], "evidence"))
        for domain in domains:
            if cb["id"] in domain.get("implementations_by_codebase", {}) and domain["id"] in domain_nodes:
                edges.append(edge(f"domain-code:{domain['id']}:{cb['id']}", domain_nodes[domain["id"]], n["id"], "implemented in"))

    # State machines connect to entities and streams through note links, while Canvas highlights the highest-value crossings.
    for entity in entities:
        sm = entity.get("state_machine_id")
        if sm in state_nodes:
            for stream in streams:
                if entity["domain_id"] in stream.get("domain_ids", []) and stream["id"] in stream_nodes:
                    edges.append(edge(f"stream-state:{stream['id']}:{sm}", stream_nodes[stream["id"]], state_nodes[sm], "changes state", "right", "left"))
    return {"nodes": nodes, "edges": edges}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_model",type=Path); parser.add_argument("visual_model",type=Path); parser.add_argument("output",type=Path)
    parser.add_argument("--architecture-prefix",default="architecture")
    args=parser.parse_args()
    canvas=generate(read_json(args.map_model),read_json(args.visual_model),args.architecture_prefix.rstrip('/'))
    write_json(args.output,canvas); print(f"WROTE {args.output} nodes={len(canvas['nodes'])} edges={len(canvas['edges'])}")
    return 0
if __name__=="__main__": raise SystemExit(main())
