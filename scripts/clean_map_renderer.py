#!/usr/bin/env python3
"""Deterministic clean renderer for bounded overview maps.

The renderer, not the analysis agent, owns positions, colors, icon geometry,
and edge routing. It emits editable native Excalidraw primitives plus SVG/PNG
previews. No remote assets or font files are bundled.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
import hashlib
import json
import math
from pathlib import Path
from typing import Any

CANVAS_BG = "#fcfcfb"
CARD_BG = "#ffffff"
CARD_STROKE = "#d8dee7"
GROUP_BG = "#f7f8fa"
GROUP_STROKE = "#e5e7eb"
TEXT = "#1f2937"
MUTED = "#667085"
EDGE = "#9aa4b2"

KIND_ACCENT = {
    "entry": "#64748b",
    "schedule": "#b7791f",
    "actor": "#c05621",
    "process": "#3b82f6",
    "decision": "#7c3aed",
    "service": "#2563eb",
    "store": "#059669",
    "external": "#0284c7",
    "outcome": "#16a34a",
    "risk": "#dc2626",
}
KIND_SOFT = {
    "entry": "#f1f5f9",
    "schedule": "#fff7e6",
    "actor": "#fff1e8",
    "process": "#eff6ff",
    "decision": "#f5f3ff",
    "service": "#eff6ff",
    "store": "#ecfdf5",
    "external": "#f0f9ff",
    "outcome": "#f0fdf4",
    "risk": "#fef2f2",
}
EDGE_STYLE = {
    "normal": (EDGE, "solid", 1.35),
    "conditional": ("#7c3aed", "solid", 1.45),
    "async": ("#0284c7", "dashed", 1.4),
    "data": ("#059669", "solid", 1.4),
    "error": ("#dc2626", "dashed", 1.45),
    "recovery": ("#b45309", "dashed", 1.45),
}


@dataclass
class NodeBox:
    node: dict[str, Any]
    x: float
    y: float
    width: float
    height: float
    group_id: str


@dataclass
class GroupBox:
    group: dict[str, Any]
    x: float
    y: float
    width: float
    height: float


def _hash_text(*parts: object) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def element_id(*parts: object, prefix: str = "el") -> str:
    return f"{prefix}-{_hash_text(*parts)[:14]}"


def seed_for(*parts: object) -> int:
    return int(_hash_text(*parts)[:8], 16) & 0x7FFFFFFF


def common(element_type: str, eid: str, x: float, y: float, width: float, height: float) -> dict[str, Any]:
    return {
        "id": eid,
        "type": element_type,
        "x": round(x, 2),
        "y": round(y, 2),
        "width": round(width, 2),
        "height": round(height, 2),
        "angle": 0,
        "strokeColor": TEXT,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": seed_for(eid),
        "version": 1,
        "versionNonce": seed_for(eid, "nonce"),
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
    }


def rect(eid: str, x: float, y: float, w: float, h: float, *, stroke: str, fill: str, stroke_width: float = 1, opacity: int = 100, radius: bool = True, group_ids: list[str] | None = None, link: str | None = None) -> dict[str, Any]:
    el = common("rectangle", eid, x, y, w, h)
    el.update({
        "strokeColor": stroke,
        "backgroundColor": fill,
        "strokeWidth": stroke_width,
        "opacity": opacity,
        "roundness": {"type": 3} if radius else None,
        "groupIds": group_ids or [],
        "link": link,
    })
    return el


def ellipse(eid: str, x: float, y: float, w: float, h: float, *, stroke: str, fill: str = "transparent", stroke_width: float = 1.2, group_ids: list[str] | None = None) -> dict[str, Any]:
    el = common("ellipse", eid, x, y, w, h)
    el.update({"strokeColor": stroke, "backgroundColor": fill, "strokeWidth": stroke_width, "groupIds": group_ids or []})
    return el


def diamond(eid: str, x: float, y: float, w: float, h: float, *, stroke: str, fill: str = "transparent", stroke_width: float = 1.2, group_ids: list[str] | None = None) -> dict[str, Any]:
    el = common("diamond", eid, x, y, w, h)
    el.update({"strokeColor": stroke, "backgroundColor": fill, "strokeWidth": stroke_width, "groupIds": group_ids or []})
    return el


def text_el(eid: str, x: float, y: float, w: float, h: float, text: str, *, size: int, color: str = TEXT, align: str = "left", weight: str = "normal", group_ids: list[str] | None = None) -> dict[str, Any]:
    el = common("text", eid, x, y, w, h)
    el.update({
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fontSize": size,
        "fontFamily": 1,
        "text": text,
        "textAlign": align,
        "verticalAlign": "top",
        "containerId": None,
        "originalText": text,
        "autoResize": False,
        "lineHeight": 1.25,
        "groupIds": group_ids or [],
        "customData": {"fontWeight": weight},
    })
    return el


def line_el(eid: str, points_abs: list[tuple[float, float]], *, stroke: str, stroke_width: float = 1.2, stroke_style: str = "solid", arrow: bool = False, group_ids: list[str] | None = None, custom_data: dict[str, Any] | None = None) -> dict[str, Any]:
    min_x = min(p[0] for p in points_abs)
    min_y = min(p[1] for p in points_abs)
    max_x = max(p[0] for p in points_abs)
    max_y = max(p[1] for p in points_abs)
    rel = [[round(x - min_x, 2), round(y - min_y, 2)] for x, y in points_abs]
    el = common("arrow" if arrow else "line", eid, min_x, min_y, max_x - min_x, max_y - min_y)
    el.update({
        "strokeColor": stroke,
        "strokeWidth": stroke_width,
        "strokeStyle": stroke_style,
        "roundness": {"type": 2},
        "points": rel,
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": "arrow" if arrow else None,
        "elbowed": False,
        "groupIds": group_ids or [],
        "customData": custom_data or {},
    })
    return el


def node_height(node: dict[str, Any]) -> float:
    embeds = node.get("embeds", []) if isinstance(node.get("embeds"), list) else []
    rows = math.ceil(min(4, len(embeds)) / 2)
    return 72 + rows * 25


def compute_layout(data: dict[str, Any]) -> dict[str, Any]:
    groups = sorted(data.get("groups", []), key=lambda g: (g.get("order", 0), g.get("label", "")))
    group_index = {g["id"]: i for i, g in enumerate(groups)}
    focus_order = {nid: i for i, nid in enumerate(data.get("focusPath", []))}
    nodes_by_group: dict[str, list[dict[str, Any]]] = {g["id"]: [] for g in groups}
    for index, node in enumerate(data.get("nodes", [])):
        node = dict(node)
        node["_inputOrder"] = index
        nodes_by_group.setdefault(node.get("groupId", groups[0]["id"] if groups else "main"), []).append(node)
    for gid, items in nodes_by_group.items():
        items.sort(key=lambda n: (focus_order.get(n["id"], 9999), -int(n.get("importance", 3)), n["_inputOrder"]))

    margin_x = 80
    top = 170
    group_w = 260
    group_gap = 118
    card_w = 220
    inner_x = 20
    header_h = 52
    card_gap = 22
    bottom_pad = 24
    group_boxes: list[GroupBox] = []
    node_boxes: list[NodeBox] = []
    for gi, group in enumerate(groups):
        x = margin_x + gi * (group_w + group_gap)
        y = top
        cursor_y = y + header_h
        items = nodes_by_group.get(group["id"], [])
        for node in items:
            h = node_height(node)
            node_boxes.append(NodeBox(node=node, x=x + inner_x, y=cursor_y, width=card_w, height=h, group_id=group["id"]))
            cursor_y += h + card_gap
        height = max(150, cursor_y - y - (card_gap if items else 0) + bottom_pad)
        group_boxes.append(GroupBox(group=group, x=x, y=y, width=group_w, height=height))
    node_by_id = {b.node["id"]: b for b in node_boxes}
    group_by_id = {g.group["id"]: g for g in group_boxes}
    max_bottom = max((g.y + g.height for g in group_boxes), default=top + 200)

    pair_channels: dict[tuple[str, str], float] = {}
    pair_counts: dict[tuple[str, str], int] = {}
    back_count = 0
    rendered_edges: list[dict[str, Any]] = []
    for ei, edge in enumerate(data.get("edges", [])):
        source = node_by_id.get(edge.get("from"))
        target = node_by_id.get(edge.get("to"))
        if not source or not target:
            continue
        sg = group_index.get(source.group_id, 0)
        tg = group_index.get(target.group_id, 0)
        kind = edge.get("kind", "normal")
        if source.group_id == target.group_id:
            if target.y >= source.y:
                sx, sy = source.x + source.width / 2, source.y + source.height
                tx, ty = target.x + target.width / 2, target.y
                mid_y = (sy + ty) / 2
                points = [(sx, sy), (sx, mid_y), (tx, mid_y), (tx, ty)]
            else:
                gutter = group_by_id[source.group_id].x + group_by_id[source.group_id].width + 28 + (ei % 3) * 10
                sx, sy = source.x + source.width, source.y + source.height / 2
                tx, ty = target.x + target.width, target.y + target.height / 2
                points = [(sx, sy), (gutter, sy), (gutter, ty), (tx, ty)]
        elif tg > sg and kind not in {"recovery"}:
            sx, sy = source.x + source.width, source.y + source.height / 2
            tx, ty = target.x, target.y + target.height / 2
            pair = (source.group_id, target.group_id)
            pair_counts[pair] = pair_counts.get(pair, 0) + 1
            if pair not in pair_channels:
                right = group_by_id[source.group_id].x + group_by_id[source.group_id].width
                left = group_by_id[target.group_id].x
                pair_channels[pair] = (right + left) / 2
            channel_x = pair_channels[pair] + (pair_counts[pair] - 1) * 7
            points = [(sx, sy), (channel_x, sy), (channel_x, ty), (tx, ty)]
        else:
            back_count += 1
            route_y = max_bottom + 55 + (back_count - 1) * 34
            sx, sy = source.x + source.width / 2, source.y + source.height
            tx, ty = target.x + target.width / 2, target.y + target.height
            points = [(sx, sy), (sx, route_y), (tx, route_y), (tx, ty)]
        rendered_edges.append({"edge": edge, "points": points})

    width = margin_x * 2 + max(1, len(groups)) * group_w + max(0, len(groups) - 1) * group_gap
    height = max_bottom + 110 + back_count * 34
    return {
        "width": width,
        "height": height,
        "groups": [g.__dict__ for g in group_boxes],
        "nodes": [n.__dict__ for n in node_boxes],
        "edges": rendered_edges,
    }


def longest_segment_anchor(points: list[tuple[float, float]]) -> tuple[float, float]:
    best_len = -1.0
    best = (points[0][0], points[0][1])
    for a, b in zip(points, points[1:]):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        if length > best_len:
            best_len = length
            best = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return best


def icon_elements(kind: str, x: float, y: float, color: str, group_id: str) -> list[dict[str, Any]]:
    gid = [group_id]
    cx, cy = x + 14, y + 14
    els: list[dict[str, Any]] = []
    if kind == "entry":
        els.append(line_el(element_id(group_id, "entry-arrow"), [(x+7, cy), (x+19, cy)], stroke=color, stroke_width=1.5, arrow=True, group_ids=gid))
        els.append(line_el(element_id(group_id, "entry-bracket"), [(x+19, y+8), (x+22, y+8), (x+22, y+20), (x+19, y+20)], stroke=color, stroke_width=1.4, group_ids=gid))
    elif kind == "schedule":
        els.append(ellipse(element_id(group_id, "clock"), x+6, y+6, 16, 16, stroke=color, stroke_width=1.4, group_ids=gid))
        els.append(line_el(element_id(group_id, "hands"), [(cx, cy), (cx, y+9), (x+18, cy)], stroke=color, stroke_width=1.3, group_ids=gid))
    elif kind == "actor":
        els.append(ellipse(element_id(group_id, "head"), x+10, y+6, 8, 8, stroke=color, stroke_width=1.3, group_ids=gid))
        els.append(line_el(element_id(group_id, "body"), [(x+7, y+22), (x+7, y+19), (x+10, y+16), (x+18, y+16), (x+21, y+19), (x+21, y+22)], stroke=color, stroke_width=1.3, group_ids=gid))
    elif kind == "decision":
        els.append(diamond(element_id(group_id, "diamond"), x+7, y+7, 14, 14, stroke=color, stroke_width=1.4, group_ids=gid))
    elif kind == "store":
        els.append(ellipse(element_id(group_id, "db-top"), x+7, y+6, 14, 6, stroke=color, stroke_width=1.3, group_ids=gid))
        els.append(line_el(element_id(group_id, "db-body"), [(x+7, y+9), (x+7, y+19), (x+9, y+22), (x+19, y+22), (x+21, y+19), (x+21, y+9)], stroke=color, stroke_width=1.3, group_ids=gid))
        els.append(line_el(element_id(group_id, "db-mid"), [(x+8, y+14), (x+20, y+14)], stroke=color, stroke_width=1.0, group_ids=gid))
    elif kind == "external":
        els.append(ellipse(element_id(group_id, "globe"), x+6, y+6, 16, 16, stroke=color, stroke_width=1.3, group_ids=gid))
        els.append(line_el(element_id(group_id, "globe-v"), [(cx, y+6), (cx-3, cy), (cx, y+22), (cx+3, cy), (cx, y+6)], stroke=color, stroke_width=1.0, group_ids=gid))
        els.append(line_el(element_id(group_id, "globe-h"), [(x+7, cy), (x+21, cy)], stroke=color, stroke_width=1.0, group_ids=gid))
    elif kind == "outcome":
        els.append(ellipse(element_id(group_id, "ok-circle"), x+6, y+6, 16, 16, stroke=color, stroke_width=1.3, group_ids=gid))
        els.append(line_el(element_id(group_id, "check"), [(x+10, cy), (x+13, y+18), (x+19, y+10)], stroke=color, stroke_width=1.6, group_ids=gid))
    elif kind == "risk":
        els.append(line_el(element_id(group_id, "triangle"), [(cx, y+5), (x+23, y+22), (x+5, y+22), (cx, y+5)], stroke=color, stroke_width=1.3, group_ids=gid))
        els.append(line_el(element_id(group_id, "risk-mark"), [(cx, y+10), (cx, y+16)], stroke=color, stroke_width=1.4, group_ids=gid))
        els.append(ellipse(element_id(group_id, "risk-dot"), cx-1, y+18, 2, 2, stroke=color, fill=color, stroke_width=1, group_ids=gid))
    elif kind == "service":
        els.append(rect(element_id(group_id, "service-box"), x+6, y+7, 16, 14, stroke=color, fill="transparent", stroke_width=1.3, radius=True, group_ids=gid))
        for i in range(3):
            els.append(ellipse(element_id(group_id, "service-dot", i), x+9+i*5, y+13, 2, 2, stroke=color, fill=color, stroke_width=1, group_ids=gid))
    else:  # process
        for i in range(3):
            els.append(ellipse(element_id(group_id, "process-dot", i), x+6+i*8, y+11, 6, 6, stroke=color, fill="transparent", stroke_width=1.2, group_ids=gid))
        els.append(line_el(element_id(group_id, "process-line"), [(x+12, cy), (x+14, cy), (x+20, cy)], stroke=color, stroke_width=1.0, group_ids=gid))
    return els


def build_excalidraw(data: dict[str, Any], layout: dict[str, Any]) -> dict[str, Any]:
    elements: list[dict[str, Any]] = []
    project = data.get("project", {})
    title = str(project.get("name", "Codebase map"))
    question = str(data.get("question", ""))
    elements.append(text_el(element_id("title"), 80, 44, max(440, len(title)*18), 38, title, size=27, color=TEXT, weight="600"))
    elements.append(text_el(element_id("question"), 80, 86, max(680, len(question)*10), 28, question, size=14, color=MUTED))
    elements.append(text_el(element_id("legend"), max(80, layout["width"]-610), 58, 530, 22, "입력  ·  처리  ·  판단  ·  저장  ·  외부  ·  결과  ·  복구", size=11, color=MUTED, align="right"))

    # Quiet group surfaces.
    for gb in layout["groups"]:
        group = gb["group"]
        gid = element_id("group", group["id"])
        elements.append(rect(gid, gb["x"], gb["y"], gb["width"], gb["height"], stroke=GROUP_STROKE, fill=GROUP_BG, stroke_width=1, opacity=82, radius=True, group_ids=[gid]))
        elements.append(text_el(element_id(group["id"], "label"), gb["x"]+18, gb["y"]+17, gb["width"]-36, 20, str(group.get("label", group["id"])).upper(), size=12, color=MUTED, weight="600", group_ids=[gid]))

    # Edges are behind cards.
    for item in layout["edges"]:
        edge = item["edge"]
        points = [(float(x), float(y)) for x, y in item["points"]]
        color, style, sw = EDGE_STYLE.get(edge.get("kind", "normal"), EDGE_STYLE["normal"])
        eid = element_id("edge", edge.get("id"), edge.get("from"), edge.get("to"))
        elements.append(line_el(eid, points, stroke=color, stroke_width=sw, stroke_style=style, arrow=True, custom_data={"role": "edge", "edgeKind": edge.get("kind", "normal")}))
        label = str(edge.get("label", "")).strip()
        if label:
            ax, ay = longest_segment_anchor(points)
            pill_w = min(164, max(42, 13 + len(label) * 7.2))
            pill_h = 22
            pill_id = element_id(eid, "label-pill")
            elements.append(rect(pill_id, ax-pill_w/2, ay-pill_h/2, pill_w, pill_h, stroke="#eef0f3", fill=CANVAS_BG, stroke_width=0.8, opacity=100, radius=True, group_ids=[pill_id]))
            elements.append(text_el(element_id(eid, "label"), ax-pill_w/2+6, ay-7, pill_w-12, 17, label, size=11, color=color, align="center", group_ids=[pill_id]))

    focus_index = {nid: i+1 for i, nid in enumerate(data.get("focusPath", []))}
    # Cards and native vector icons.
    for nb in layout["nodes"]:
        node = nb["node"]
        kind = node.get("kind", "process")
        accent = KIND_ACCENT.get(kind, KIND_ACCENT["process"])
        soft = KIND_SOFT.get(kind, KIND_SOFT["process"])
        card_gid = element_id("node-group", node["id"])
        card_id = element_id("node", node["id"])
        link = node.get("link") if isinstance(node.get("link"), str) else None
        elements.append(rect(card_id, nb["x"], nb["y"], nb["width"], nb["height"], stroke=CARD_STROKE, fill=CARD_BG, stroke_width=1.15, radius=True, group_ids=[card_gid], link=link))
        elements.append(rect(element_id(node["id"], "accent"), nb["x"], nb["y"]+10, 4, nb["height"]-20, stroke=accent, fill=accent, stroke_width=0, radius=True, group_ids=[card_gid]))
        chip_x, chip_y = nb["x"]+14, nb["y"]+14
        elements.append(rect(element_id(node["id"], "icon-chip"), chip_x, chip_y, 28, 28, stroke=soft, fill=soft, stroke_width=0.8, radius=True, group_ids=[card_gid]))
        elements.extend(icon_elements(kind, chip_x, chip_y, accent, card_gid))
        elements.append(text_el(element_id(node["id"], "title"), nb["x"]+52, nb["y"]+12, nb["width"]-72, 22, str(node.get("label", "")), size=16, color=TEXT, weight="600", group_ids=[card_gid]))
        sub = str(node.get("sub", "")).strip()
        if sub:
            elements.append(text_el(element_id(node["id"], "sub"), nb["x"]+52, nb["y"]+37, nb["width"]-68, 18, sub, size=11, color=MUTED, group_ids=[card_gid]))
        if node["id"] in focus_index:
            number = str(focus_index[node["id"]])
            elements.append(text_el(element_id(node["id"], "step"), nb["x"]+nb["width"]-28, nb["y"]+14, 16, 16, number, size=10, color=MUTED, align="center", weight="600", group_ids=[card_gid]))
        embeds = node.get("embeds", []) if isinstance(node.get("embeds"), list) else []
        if embeds:
            row_y = nb["y"] + 62
            col_x = nb["x"] + 14
            for i, embed in enumerate(embeds[:4]):
                if i and i % 2 == 0:
                    row_y += 25
                    col_x = nb["x"] + 14
                label = str(embed.get("label", ""))
                kind_label = str(embed.get("kind", "technology"))
                pill_w = min(94, max(66, 26 + len(label) * 5.5))
                pill_id = element_id(node["id"], "embed", i)
                elements.append(rect(pill_id, col_x, row_y, pill_w, 19, stroke="#e7eaf0", fill="#f9fafb", stroke_width=0.8, radius=True, group_ids=[card_gid]))
                elements.append(ellipse(element_id(pill_id, "dot"), col_x+7, row_y+7, 5, 5, stroke=accent, fill=accent, stroke_width=0.8, group_ids=[card_gid]))
                display = label if len(label) <= 13 else label[:12] + "…"
                elements.append(text_el(element_id(pill_id, "text"), col_x+16, row_y+3, pill_w-20, 14, display, size=9, color=MUTED, group_ids=[card_gid]))
                col_x += pill_w + 8

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "im-code-map-v5.3.0",
        "elements": elements,
        "appState": {
            "viewBackgroundColor": CANVAS_BG,
            "gridSize": 20,
            "gridStep": 5,
            "gridModeEnabled": False,
            "currentItemRoughness": 0,
            "currentItemStrokeWidth": 1,
        },
        "files": {},
        "imCodeMap": {
            "version": "5.3.0",
            "renderer": "clean-overview-v1",
            "mapHash": data.get("mapHash"),
            "question": data.get("question"),
        },
    }


def rounded_path(points: list[tuple[float, float]], radius: float = 10) -> str:
    if len(points) < 2:
        return ""
    if len(points) == 2:
        return f"M {points[0][0]} {points[0][1]} L {points[1][0]} {points[1][1]}"
    def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.hypot(b[0]-a[0], b[1]-a[1])
    def toward(a: tuple[float, float], b: tuple[float, float], amount: float) -> tuple[float, float]:
        length = dist(a, b) or 1
        return (a[0]+(b[0]-a[0])*amount/length, a[1]+(b[1]-a[1])*amount/length)
    d = f"M {points[0][0]} {points[0][1]}"
    for i in range(1, len(points)-1):
        prev, cur, nxt = points[i-1], points[i], points[i+1]
        a = toward(cur, prev, min(radius, dist(prev, cur)/2))
        b = toward(cur, nxt, min(radius, dist(cur, nxt)/2))
        d += f" L {a[0]} {a[1]} Q {cur[0]} {cur[1]} {b[0]} {b[1]}"
    d += f" L {points[-1][0]} {points[-1][1]}"
    return d


def svg_document(data: dict[str, Any], layout: dict[str, Any]) -> str:
    width, height = int(layout["width"]), int(layout["height"])
    project = data.get("project", {})
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><filter id="card" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#101828" flood-opacity="0.05"/></filter><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#9aa4b2" stroke-width="1.2"/></marker></defs>',
        f'<rect width="100%" height="100%" fill="{CANVAS_BG}"/>',
        f'<text x="80" y="70" font-family="Arial, sans-serif" font-size="27" font-weight="600" fill="{TEXT}">{escape(str(project.get("name", "Codebase map")))}</text>',
        f'<text x="80" y="108" font-family="Arial, sans-serif" font-size="14" fill="{MUTED}">{escape(str(data.get("question", "")))}</text>',
    ]
    for gb in layout["groups"]:
        g = gb["group"]
        parts.append(f'<rect x="{gb["x"]}" y="{gb["y"]}" width="{gb["width"]}" height="{gb["height"]}" rx="18" fill="{GROUP_BG}" stroke="{GROUP_STROKE}"/>')
        parts.append(f'<text x="{gb["x"]+18}" y="{gb["y"]+31}" font-family="Arial, sans-serif" font-size="12" font-weight="600" fill="{MUTED}">{escape(str(g.get("label", g["id"])).upper())}</text>')
    for item in layout["edges"]:
        edge = item["edge"]
        points = [(float(x), float(y)) for x, y in item["points"]]
        color, style, sw = EDGE_STYLE.get(edge.get("kind", "normal"), EDGE_STYLE["normal"])
        dash = ' stroke-dasharray="6 5"' if style == "dashed" else ""
        parts.append(f'<path d="{rounded_path(points)}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow)"{dash}/>')
        label = str(edge.get("label", "")).strip()
        if label:
            ax, ay = longest_segment_anchor(points)
            pill_w = min(164, max(42, 13 + len(label)*7.2))
            parts.append(f'<rect x="{ax-pill_w/2}" y="{ay-11}" width="{pill_w}" height="22" rx="11" fill="{CANVAS_BG}" stroke="#eef0f3"/>')
            parts.append(f'<text x="{ax}" y="{ay+4}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="{color}">{escape(label)}</text>')
    focus_index = {nid: i+1 for i, nid in enumerate(data.get("focusPath", []))}
    for nb in layout["nodes"]:
        node = nb["node"]
        kind = node.get("kind", "process")
        accent = KIND_ACCENT.get(kind, KIND_ACCENT["process"])
        soft = KIND_SOFT.get(kind, KIND_SOFT["process"])
        x, y, w, h = nb["x"], nb["y"], nb["width"], nb["height"]
        parts.append(f'<g filter="url(#card)"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{CARD_BG}" stroke="{CARD_STROKE}" stroke-width="1.15"/><rect x="{x}" y="{y+10}" width="4" height="{h-20}" rx="2" fill="{accent}"/></g>')
        parts.append(f'<rect x="{x+14}" y="{y+14}" width="28" height="28" rx="9" fill="{soft}"/>')
        # Clean preview glyph: small semantic dot and letter; Excalidraw carries native line icons.
        parts.append(f'<circle cx="{x+28}" cy="{y+28}" r="5" fill="none" stroke="{accent}" stroke-width="1.5"/>')
        parts.append(f'<text x="{x+52}" y="{y+29}" font-family="Arial, sans-serif" font-size="16" font-weight="600" fill="{TEXT}">{escape(str(node.get("label", "")))}</text>')
        sub = str(node.get("sub", "")).strip()
        if sub:
            parts.append(f'<text x="{x+52}" y="{y+50}" font-family="Arial, sans-serif" font-size="11" fill="{MUTED}">{escape(sub)}</text>')
        if node["id"] in focus_index:
            parts.append(f'<text x="{x+w-20}" y="{y+25}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" font-weight="600" fill="{MUTED}">{focus_index[node["id"]]}</text>')
        embeds = node.get("embeds", []) if isinstance(node.get("embeds"), list) else []
        if embeds:
            row_y, col_x = y+62, x+14
            for i, embed in enumerate(embeds[:4]):
                if i and i%2 == 0:
                    row_y += 25; col_x = x+14
                label = str(embed.get("label", ""))
                display = label if len(label) <= 13 else label[:12]+"…"
                pw = min(94, max(66, 26+len(label)*5.5))
                parts.append(f'<rect x="{col_x}" y="{row_y}" width="{pw}" height="19" rx="9.5" fill="#f9fafb" stroke="#e7eaf0"/>')
                parts.append(f'<circle cx="{col_x+9.5}" cy="{row_y+9.5}" r="2.5" fill="{accent}"/>')
                parts.append(f'<text x="{col_x+16}" y="{row_y+13}" font-family="Arial, sans-serif" font-size="9" fill="{MUTED}">{escape(display)}</text>')
                col_x += pw+8
    parts.append('</svg>')
    return "".join(parts)


def write_png(svg: str, path: Path, width: int, height: int) -> None:
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(path), output_width=width, output_height=height)
        return
    except Exception:
        pass
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new("RGB", (width, height), CANVAS_BG)
    draw = ImageDraw.Draw(image)
    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    font_path = next((p for p in font_paths if Path(p).exists()), None)
    def f(size: int):
        return ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
    draw.text((80, 44), str(data_global.get("project", {}).get("name", "Codebase map")), fill=TEXT, font=f(27))
    draw.text((80, 86), str(data_global.get("question", "")), fill=MUTED, font=f(14))
    for gb in layout_global["groups"]:
        draw.rounded_rectangle((gb["x"], gb["y"], gb["x"]+gb["width"], gb["y"]+gb["height"]), radius=18, fill=GROUP_BG, outline=GROUP_STROKE, width=1)
        draw.text((gb["x"]+18, gb["y"]+17), str(gb["group"].get("label", "")).upper(), fill=MUTED, font=f(12))
    for item in layout_global["edges"]:
        edge = item["edge"]
        color, style, sw = EDGE_STYLE.get(edge.get("kind", "normal"), EDGE_STYLE["normal"])
        points = [(int(x), int(y)) for x,y in item["points"]]
        draw.line(points, fill=color, width=max(1, int(round(sw))))
    for nb in layout_global["nodes"]:
        node = nb["node"]
        accent = KIND_ACCENT.get(node.get("kind", "process"), KIND_ACCENT["process"])
        x,y,w,h = int(nb["x"]),int(nb["y"]),int(nb["width"]),int(nb["height"])
        draw.rounded_rectangle((x,y,x+w,y+h), radius=14, fill=CARD_BG, outline=CARD_STROKE, width=1)
        draw.rounded_rectangle((x,y+10,x+4,y+h-10), radius=2, fill=accent)
        draw.rounded_rectangle((x+14,y+14,x+42,y+42), radius=9, fill=KIND_SOFT.get(node.get("kind","process"),"#eff6ff"))
        draw.ellipse((x+23,y+23,x+33,y+33), outline=accent, width=2)
        draw.text((x+52,y+12), str(node.get("label","")), fill=TEXT, font=f(16))
        if node.get("sub"):
            draw.text((x+52,y+36), str(node.get("sub")), fill=MUTED, font=f(11))
    image.save(path)


# Fallback renderer uses these module globals only when cairosvg is unavailable.
data_global: dict[str, Any] = {}
layout_global: dict[str, Any] = {}


def render_bundle(data: dict[str, Any], output_excalidraw: str | Path, output_svg: str | Path | None = None, output_png: str | Path | None = None, layout_json: str | Path | None = None) -> dict[str, Any]:
    global data_global, layout_global
    layout = compute_layout(data)
    excalidraw = build_excalidraw(data, layout)
    exc_path = Path(output_excalidraw)
    exc_path.parent.mkdir(parents=True, exist_ok=True)
    exc_path.write_text(json.dumps(excalidraw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    svg = svg_document(data, layout)
    if output_svg:
        svg_path = Path(output_svg); svg_path.parent.mkdir(parents=True, exist_ok=True); svg_path.write_text(svg, encoding="utf-8")
    if output_png:
        data_global, layout_global = data, layout
        png_path = Path(output_png); png_path.parent.mkdir(parents=True, exist_ok=True)
        write_png(svg, png_path, int(layout["width"]), int(layout["height"]))
    if layout_json:
        clean_layout = {
            "width": layout["width"], "height": layout["height"],
            "groups": [{**g, "group": g["group"]} for g in layout["groups"]],
            "nodes": [{**n, "node": n["node"]} for n in layout["nodes"]],
            "edges": layout["edges"],
        }
        lp = Path(layout_json); lp.parent.mkdir(parents=True, exist_ok=True)
        lp.write_text(json.dumps(clean_layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"excalidraw": str(exc_path), "width": layout["width"], "height": layout["height"], "elements": len(excalidraw["elements"])}
