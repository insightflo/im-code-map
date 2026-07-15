#!/usr/bin/env python3
"""Compose canonical child drawings into a curated infinite-canvas Deep Atlas.

The master remains a merged, editable Excalidraw scene. v5.1 adds a navigable
section index and a balanced grid instead of blindly trusting stale x/y offsets.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from excalidraw_design_system import chip_elements, load_design, rectangle, shadow_element, text_element
from im_code_map_common import read_json, scene_bounds, stable_id, write_json


DEFAULT_SCALE = {
    "domain-commerce-overview": 0.86,
    "stream-member-place-order": 0.65,
    "state-product-order-eligibility": 0.82,
    "stream-browse-orderable-products": 0.76,
    "stream-cancel-order": 0.76,
}


def remap_scene(
    elements: list[dict[str, Any]], namespace: str, scale: float, target_x: float, target_y: float
) -> tuple[list[dict[str, Any]], tuple[float, float, float, float]]:
    active = [e for e in elements if not e.get("isDeleted")]
    bx, by, bw, bh = scene_bounds(active)
    dx = target_x - bx * scale
    dy = target_y - by * scale
    id_map = {e["id"]: stable_id(e.get("type", "el")[:3], namespace + ":" + e["id"]) for e in active}
    group_map: dict[str, str] = {}
    for element in active:
        for gid in element.get("groupIds", []) or []:
            group_map.setdefault(gid, stable_id("grp", namespace + ":" + gid))

    out: list[dict[str, Any]] = []
    for original in active:
        e = copy.deepcopy(original)
        e["id"] = id_map[original["id"]]
        e["x"] = round(float(e.get("x", 0)) * scale + dx, 2)
        e["y"] = round(float(e.get("y", 0)) * scale + dy, 2)
        e["width"] = round(float(e.get("width", 0)) * scale, 2)
        e["height"] = round(float(e.get("height", 0)) * scale, 2)
        if "fontSize" in e:
            e["fontSize"] = max(12, int(float(e["fontSize"]) * scale))
            e["baseline"] = max(1, int(float(e.get("baseline", e["fontSize"])) * scale))
        if "points" in e:
            e["points"] = [[round(float(p[0]) * scale, 2), round(float(p[1]) * scale, 2)] for p in e["points"]]
        if e.get("frameId"):
            e["frameId"] = id_map.get(e["frameId"])
        if e.get("containerId"):
            e["containerId"] = id_map.get(e["containerId"])
        e["groupIds"] = [group_map.get(gid, gid) for gid in (e.get("groupIds") or [])]
        if e.get("boundElements"):
            e["boundElements"] = [{**b, "id": id_map.get(b.get("id"), b.get("id"))} for b in e["boundElements"]]
        for binding_key in ("startBinding", "endBinding"):
            if e.get(binding_key):
                e[binding_key]["elementId"] = id_map.get(e[binding_key].get("elementId"), e[binding_key].get("elementId"))
                if e[binding_key].get("fixedPoint"):
                    e[binding_key]["fixedPoint"] = [float(v) * scale for v in e[binding_key]["fixedPoint"]]
        custom = e.setdefault("customData", {})
        custom.setdefault("imCodeMap", {})["compositionNamespace"] = namespace
        out.append(e)
    return out, (target_x, target_y, bw * scale, bh * scale)


def section_shell(
    key: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    title: str,
    diagram_id: str,
    child_link: str,
    index: int,
    theme: dict[str, Any],
) -> list[dict[str, Any]]:
    colors = [theme["primary"], theme["blue"], theme["purple"], theme["info"], theme["pink"]]
    accent = colors[(index - 1) % len(colors)]
    elements: list[dict[str, Any]] = [
        shadow_element(key + ":shadow", x, y, w, h, theme=theme),
        rectangle(
            key + ":bg", x, y, w, h, theme=theme, stroke=theme["border"],
            background=theme["surface"], stroke_width=1.5, role="composition-section",
        ),
        rectangle(
            key + ":accent", x, y, 10, h, theme=theme, stroke=accent,
            background=accent, stroke_width=0, role="composition-section-accent",
        ),
    ]
    chips, chip_w = chip_elements(
        key + ":index", x + 28, y + 22, f"MAP {index}", theme=theme,
        color=accent, background=theme["surface_alt"], font_size=11,
        min_width=78, role="master-index-chip",
    )
    elements.extend(chips)
    elements.extend([
        text_element(
            key + ":title", x + 28 + chip_w + 16, y + 18, title,
            font_size=24, width=max(300, w - 520), height=42, color=theme["ink"],
            align="left", valign="middle", font_family=theme["font_family"],
            custom_data={"imCodeMap": {"role": "composition-section-title", "diagramId": diagram_id}},
        ),
        text_element(
            key + ":open", x + w - 410, y + 19, f"↗ Open child: {diagram_id}",
            font_size=13, width=382, height=38, color=accent, align="right", valign="middle",
            link=child_link, font_family=theme["font_family"],
            custom_data={"imCodeMap": {"role": "composition-child-link", "diagramId": diagram_id}},
        ),
    ])
    return elements


def build_index(
    composition: dict[str, Any], placements: list[dict[str, Any]], *, theme: dict[str, Any], width: float, link_prefix: str
) -> list[dict[str, Any]]:
    elements: list[dict[str, Any]] = []
    elements.append(text_element(
        "master-eyebrow:" + composition["id"], 60, 38, "DEEP ATLAS · INFINITE CANVAS",
        font_size=13, width=330, height=30, color=theme["primary"], align="left",
        valign="middle", font_family=theme["font_family"],
        custom_data={"imCodeMap": {"role": "profile-chip-text"}},
    ))
    elements.append(text_element(
        "master-title:" + composition["id"], 60, 80, composition["title"],
        font_size=46, width=1400, height=66, color=theme["ink"], align="left",
        valign="middle", font_family=theme["font_family"],
        custom_data={"imCodeMap": {"role": "diagram-title"}},
    ))
    elements.append(text_element(
        "master-subtitle:" + composition["id"], 60, 148,
        "도메인 경계 → 핵심 업무 흐름 → 상태와 보상 → 지원 흐름 순서로 확대해 읽습니다.",
        font_size=17, width=1450, height=42, color=theme["muted"], align="left",
        valign="middle", font_family=theme["font_family"],
        custom_data={"imCodeMap": {"role": "diagram-purpose"}},
    ))

    card_gap = 22.0
    card_w = (width - 120 - card_gap * (len(placements) - 1)) / max(1, len(placements))
    y = 224.0
    colors = [theme["primary"], theme["blue"], theme["purple"], theme["info"], theme["pink"]]
    for idx, placement in enumerate(placements, start=1):
        x = 60 + (idx - 1) * (card_w + card_gap)
        accent = colors[(idx - 1) % len(colors)]
        link = f"[[{link_prefix.rstrip('/')}/{placement['diagram_id']}.excalidraw]]"
        elements.extend([
            shadow_element(f"master-index:{idx}:shadow", x, y, card_w, 112, theme=theme),
            rectangle(
                f"master-index:{idx}:bg", x, y, card_w, 112, theme=theme,
                stroke=theme["border"], background=theme["surface"], stroke_width=1.2,
                link=link, role="master-index-card",
            ),
            rectangle(
                f"master-index:{idx}:accent", x, y, 7, 112, theme=theme,
                stroke=accent, background=accent, stroke_width=0, role="master-index-accent",
            ),
            text_element(
                f"master-index:{idx}:number", x + 22, y + 18, f"{idx:02d}",
                font_size=24, width=52, height=36, color=accent, align="left", valign="middle",
                link=link, font_family=theme["font_family"],
                custom_data={"imCodeMap": {"role": "master-index-number"}},
            ),
            text_element(
                f"master-index:{idx}:title", x + 22, y + 54, placement.get("title", placement["diagram_id"]),
                font_size=15, width=card_w - 44, height=42, color=theme["ink"], align="left",
                valign="middle", link=link, font_family=theme["font_family"],
                custom_data={"imCodeMap": {"role": "master-index-title"}},
            ),
        ])
    return elements


def compose(model: dict[str, Any], composition: dict[str, Any], child_dir: Path, link_prefix: str, theme_name: str) -> dict[str, Any]:
    theme = load_design(theme_name)
    placement_defs = list(composition.get("placements", []))
    if not placement_defs:
        raise ValueError("composition has no placements")

    child_data: dict[str, dict[str, Any]] = {}
    section_sizes: dict[str, tuple[float, float]] = {}
    for placement in placement_defs:
        diagram_id = placement["diagram_id"]
        child_path = child_dir / f"{diagram_id}.excalidraw"
        if not child_path.exists():
            raise FileNotFoundError(f"missing child diagram: {child_path}")
        child = read_json(child_path)
        child_data[diagram_id] = child
        _, _, bw, bh = scene_bounds([e for e in child.get("elements", []) if not e.get("isDeleted")])
        scale = DEFAULT_SCALE.get(diagram_id, float(placement.get("scale", 0.78)))
        section_sizes[diagram_id] = (bw * scale + 72, bh * scale + 112)

    by_id = {p["diagram_id"]: p for p in placement_defs}
    domain_id = "domain-commerce-overview" if "domain-commerce-overview" in by_id else placement_defs[0]["diagram_id"]
    primary_id = "stream-member-place-order" if "stream-member-place-order" in by_id else placement_defs[min(1, len(placement_defs)-1)]["diagram_id"]
    state_id = "state-product-order-eligibility" if "state-product-order-eligibility" in by_id else None
    browse_id = "stream-browse-orderable-products" if "stream-browse-orderable-products" in by_id else None
    cancel_id = "stream-cancel-order" if "stream-cancel-order" in by_id else None

    gap = 70.0
    left = 60.0
    top = 410.0
    positions: dict[str, tuple[float, float]] = {}
    domain_w, domain_h = section_sizes[domain_id]
    positions[domain_id] = (left, top)
    row1_right = left + domain_w
    row1_bottom = top + domain_h
    if browse_id:
        positions[browse_id] = (row1_right + gap, top)
        bw, bh = section_sizes[browse_id]
        row1_right += gap + bw
        row1_bottom = max(row1_bottom, top + bh)

    primary_y = row1_bottom + gap
    positions[primary_id] = (left, primary_y)
    primary_w, primary_h = section_sizes[primary_id]
    max_right = max(row1_right, left + primary_w)
    row3_y = primary_y + primary_h + gap
    if state_id:
        positions[state_id] = (left, row3_y)
        sw, sh = section_sizes[state_id]
        max_right = max(max_right, left + sw)
        row3_bottom = row3_y + sh
    else:
        sw = sh = 0
        row3_bottom = row3_y
    if cancel_id:
        cancel_x = left + sw + gap if state_id else left
        positions[cancel_id] = (cancel_x, row3_y)
        cw, ch = section_sizes[cancel_id]
        max_right = max(max_right, cancel_x + cw)
        row3_bottom = max(row3_bottom, row3_y + ch)

    # Any extra diagrams are appended below the curated core.
    cursor_y = row3_bottom + gap
    for placement in placement_defs:
        diagram_id = placement["diagram_id"]
        if diagram_id in positions:
            continue
        positions[diagram_id] = (left, cursor_y)
        cursor_y += section_sizes[diagram_id][1] + gap
        max_right = max(max_right, left + section_sizes[diagram_id][0])

    master_width = max(2400.0, max_right + 60)
    all_elements: list[dict[str, Any]] = []
    all_elements.extend(build_index(composition, placement_defs, theme=theme, width=master_width, link_prefix=link_prefix))
    source_diagrams: list[str] = []

    for index, placement in enumerate(placement_defs, start=1):
        diagram_id = placement["diagram_id"]
        section_x, section_y = positions[diagram_id]
        section_w, section_h = section_sizes[diagram_id]
        child_link = f"[[{link_prefix.rstrip('/')}/{diagram_id}.excalidraw]]"
        shell = section_shell(
            f"master-section:{composition['id']}:{diagram_id}", section_x, section_y,
            section_w, section_h, title=placement.get("title", diagram_id),
            diagram_id=diagram_id, child_link=child_link, index=index, theme=theme,
        )
        all_elements.extend(shell)
        scale = DEFAULT_SCALE.get(diagram_id, float(placement.get("scale", 0.78)))
        transformed, _ = remap_scene(
            child_data[diagram_id].get("elements", []), f"{composition['id']}:{diagram_id}",
            scale, section_x + 34, section_y + 82,
        )
        all_elements.extend(transformed)
        source_diagrams.append(diagram_id)

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "im-code-map-v5.1-composition",
        "elements": all_elements,
        "appState": {
            "gridSize": 20,
            "gridStep": 5,
            "gridModeEnabled": False,
            "viewBackgroundColor": theme["canvas"],
            "currentItemFontFamily": theme["font_family"],
        },
        "files": {},
        "imCodeMap": {
            "schemaVersion": "5.0.0",
            "designSystemVersion": "1.0.0",
            "theme": theme["name"],
            "diagramId": composition["id"],
            "diagramType": "master-map",
            "sourceDiagrams": source_diagrams,
            "compositionMode": "merge-elements",
            "layoutMode": "curated-grid",
            "generated": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visual_model", type=Path)
    parser.add_argument("child_dir", type=Path)
    parser.add_argument("output_dir", type=Path, nargs="?", default=None)
    parser.add_argument("--composition", action="append", dest="composition_ids")
    parser.add_argument("--link-prefix", default="architecture/atlas/excalidraw", help="Vault-relative child link prefix")
    parser.add_argument("--theme", choices=["clean", "whiteboard"], default="clean")
    args = parser.parse_args()

    model = read_json(args.visual_model)
    output_dir = args.output_dir or args.child_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = set(args.composition_ids or [])
    count = 0
    for composition in model.get("compositions", []):
        if composition.get("mode") != "merge-elements":
            continue
        if selected and composition["id"] not in selected:
            continue
        scene = compose(model, composition, args.child_dir, args.link_prefix, args.theme)
        output_path = output_dir / f"{composition['id']}.excalidraw"
        write_json(output_path, scene)
        print(f"WROTE {output_path}")
        count += 1
    if not count:
        print("WARN: no merge-elements compositions selected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
