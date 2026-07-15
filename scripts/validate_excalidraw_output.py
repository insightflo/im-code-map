#!/usr/bin/env python3
"""Validate generated Excalidraw semantics and basic visual readability."""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

from im_code_map_common import boxes_overlap, ensure_unique_ids, read_json


def custom(e: dict[str, Any]) -> dict[str, Any]:
    return (e.get("customData") or {}).get("imCodeMap") or {}


def validate(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        scene = read_json(path)
    except Exception as exc:
        return [f"invalid JSON: {exc}"], []
    if scene.get("type") != "excalidraw":
        errors.append("root type must be 'excalidraw'")
    elements = [e for e in scene.get("elements", []) if not e.get("isDeleted")]
    if not elements:
        errors.append("scene has no elements")
        return errors, warnings
    duplicates = ensure_unique_ids(elements, "element")
    if duplicates:
        errors.append(f"duplicate element ids: {duplicates[:5]}")
    by_id = {e.get("id"): e for e in elements}

    # Frames must appear after child elements, otherwise Excalidraw can render or clip them incorrectly.
    index = {e["id"]: i for i, e in enumerate(elements)}
    for e in elements:
        frame_id = e.get("frameId")
        if frame_id and frame_id not in by_id:
            errors.append(f"element {e['id']} references missing frame {frame_id}")
        elif frame_id and index[e["id"]] > index[frame_id]:
            errors.append(f"frame ordering violation: child {e['id']} appears after frame {frame_id}")

    node_shapes = {custom(e).get("nodeId"): e for e in elements if custom(e).get("role") == "node"}
    node_icons: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for element in elements:
        meta = custom(element)
        if meta.get("role") == "node-icon" and meta.get("nodeId"):
            node_icons[meta["nodeId"]].append(element)
    arrows = [e for e in elements if custom(e).get("role") == "edge"]
    edge_meta = [custom(e) for e in arrows]
    diagram_type = (scene.get("imCodeMap") or {}).get("diagramType")

    # Bindings are important for editable diagrams. Decorative floating arrows are humanity's contribution to ambiguity.
    for arrow in arrows:
        meta = custom(arrow)
        for key in ("startBinding", "endBinding"):
            binding = arrow.get(key)
            if not binding or binding.get("elementId") not in by_id:
                errors.append(f"edge {meta.get('edgeId', arrow['id'])} lacks valid {key}")
        if meta.get("from") not in node_shapes or meta.get("to") not in node_shapes:
            errors.append(f"edge {meta.get('edgeId')} references unknown logical node")

    incoming: dict[str, int] = defaultdict(int)
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for meta in edge_meta:
        incoming[meta.get("to")] += 1
        outgoing[meta.get("from")].append(meta)

    if diagram_type == "business-stream":
        kinds = defaultdict(list)
        for node_id, shape in node_shapes.items():
            kinds[custom(shape).get("kind")].append(node_id)
        if not kinds["start"]:
            errors.append("business stream has no explicit start node")
        if not kinds["end"]:
            errors.append("business stream has no terminal outcome node")
        for node_id in kinds["decision"]:
            shape = node_shapes[node_id]
            if shape.get("type") != "diamond":
                errors.append(f"decision {node_id} is not rendered as a diamond")
            branches = outgoing.get(node_id, [])
            if len(branches) < 2:
                errors.append(f"decision {node_id} has fewer than two outgoing branches")
            for branch in branches:
                if not str(branch.get("condition", "")).strip():
                    errors.append(f"decision branch {branch.get('edgeId')} has no condition")
        for node_id in kinds["start"]:
            if incoming.get(node_id):
                warnings.append(f"start node {node_id} has incoming edge(s)")
        for node_id in kinds["end"]:
            if outgoing.get(node_id):
                errors.append(f"terminal node {node_id} has outgoing edge(s)")
        for node_id in node_shapes:
            if not incoming.get(node_id) and not outgoing.get(node_id) and custom(node_shapes[node_id]).get("kind") not in {"note", "risk"}:
                errors.append(f"isolated business-stream node: {node_id}")


    # v5.1 presentation contract: generated scenes declare the design system, and human-facing
    # Focus drawings never leak raw Obsidian wiki-link syntax into visible labels.
    root_meta = scene.get("imCodeMap") or {}
    generated_source = str(scene.get("source", "")).startswith("im-code-map-v5.1") or root_meta.get("generated")
    if generated_source and root_meta.get("designSystemVersion") != "1.0.0":
        errors.append("generated scene is missing designSystemVersion=1.0.0")
    nav_text_elements = [e for e in elements if custom(e).get("role") == "navigation-button-text"]
    nav_labels: dict[str, set[str]] = defaultdict(set)
    for element in nav_text_elements:
        label = str(element.get("text", "")).strip()
        link = str(element.get("link", "")).strip()
        if label:
            nav_labels[label].add(link)
    for label, links in nav_labels.items():
        if len(links) > 1:
            errors.append(f"navigation label {label!r} points to multiple destinations; labels must identify the target")

    if diagram_type in {"human-overview", "focus-flow"}:
        visible_text = [str(e.get("text", "")) for e in elements if e.get("type") == "text"]
        if any("[[" in value or "]]" in value for value in visible_text):
            errors.append("Focus drawing exposes raw Obsidian wiki-link syntax")
        nav_buttons = [e for e in elements if custom(e).get("role") == "navigation-button"]
        if not nav_buttons:
            errors.append("Focus drawing has no compact navigation buttons")
        step_badges = [e for e in elements if custom(e).get("role") == "step-badge"]
        if not step_badges:
            errors.append("Focus drawing has no numbered reading path")
        panels = [e for e in elements if custom(e).get("role") in {"story-panel", "phase-panel"}]
        if not panels:
            errors.append("Focus drawing has no narrative section panel")

    # Every semantic card gets a native vector pictogram. Text/emoji icons are unstable across fonts and platforms.
    icon_exempt_kinds = {"note"}
    for node_id, shape in node_shapes.items():
        kind = custom(shape).get("kind")
        icons = node_icons.get(node_id, [])
        if kind not in icon_exempt_kinds and not icons:
            errors.append(f"semantic node {node_id} ({kind}) has no icon primitive")
        if any(icon.get("type") == "text" for icon in icons):
            errors.append(f"semantic node {node_id} uses a text/emoji icon instead of native vector primitives")

    # Node cards should be scannable, not a novella trapped inside a rectangle.
    for e in elements:
        meta = custom(e)
        if meta.get("role") == "node-label":
            value = str(e.get("text", ""))
            if len(value) > 300:
                errors.append(f"node label {meta.get('nodeId')} exceeds 300 characters")
            if value.count("\n") + 1 > 9:
                warnings.append(f"node label {meta.get('nodeId')} uses more than 9 lines")
            if float(e.get("fontSize", 0)) < 12:
                errors.append(f"node label {meta.get('nodeId')} font smaller than 12")

    # Detect true card overlap. Cross-frame boxes may share coordinates only in malformed output.
    logical_boxes = []
    for node_id, e in node_shapes.items():
        logical_boxes.append((node_id, e.get("frameId"), (float(e.get("x",0)), float(e.get("y",0)), float(e.get("width",0)), float(e.get("height",0)))))
    for i, (aid, aframe, abox) in enumerate(logical_boxes):
        for bid, bframe, bbox in logical_boxes[i+1:]:
            if aframe == bframe and boxes_overlap(abox, bbox, margin=8):
                errors.append(f"node overlap in same frame: {aid} vs {bid}")

    if root_meta.get("diagramType") == "master-map":
        sources = root_meta.get("sourceDiagrams", [])
        if len(sources) < 2:
            errors.append("master map must compose at least two child diagrams")
        linked_children = [e for e in elements if e.get("type") == "text" and str(e.get("text", "")).startswith("↗ Open child:") and e.get("link")]
        if len(linked_children) < len(sources):
            errors.append("master map is missing child-file navigation links")
        if root_meta.get("layoutMode") != "curated-grid":
            warnings.append("master map does not declare curated-grid layout")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()
    files = sorted(args.input.glob("*.excalidraw")) if args.input.is_dir() else [args.input]
    total_errors = total_warnings = 0
    for path in files:
        errors, warnings = validate(path)
        for message in warnings:
            print(f"WARN {path.name}: {message}")
        for message in errors:
            print(f"FAIL {path.name}: {message}")
        if not errors:
            print(f"PASS {path.name}: semantic and readability checks")
        total_errors += len(errors)
        total_warnings += len(warnings)
    print(f"SUMMARY files={len(files)} errors={total_errors} warnings={total_warnings}")
    return 1 if total_errors or (args.strict_warnings and total_warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
