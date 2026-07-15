#!/usr/bin/env python3
"""Reusable Excalidraw presentation primitives for im-code-map v5.1.

The module intentionally generates only native Excalidraw primitives. It does not
embed font-dependent emoji, vendor logos, or third-party stencil assets.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from im_code_map_common import clamp_text, estimate_text_box, stable_id, stable_int, wrap_text

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DESIGN_FILE = PACKAGE_ROOT / "templates" / "excalidraw-design-system.json"

ICON_KINDS = {
    "actor", "start", "process", "decision", "state-change", "event", "wait",
    "data", "storage", "external", "error", "compensation", "end", "domain",
    "codebase", "note", "risk", "test", "service", "api", "queue", "worker",
    "product", "order", "payment", "shield", "search", "browser", "unknown",
    "atlas", "flow", "question", "boundary",
}


def load_design(theme_name: str = "clean", path: Path | None = None) -> dict[str, Any]:
    raw = json.loads((path or DESIGN_FILE).read_text(encoding="utf-8"))
    name = theme_name if theme_name in raw["themes"] else raw.get("default_theme", "clean")
    theme = dict(raw["themes"][name])
    theme["name"] = name
    theme["semantic_map"] = raw.get("semantic", {})
    theme["edge_map"] = raw.get("edges", {})
    return theme


def semantic_style(theme: dict[str, Any], kind: str) -> tuple[str, str]:
    keys = theme.get("semantic_map", {}).get(kind, ["muted", "surface_alt"])
    return theme.get(keys[0], theme["muted"]), theme.get(keys[1], theme["surface_alt"])


def edge_style(theme: dict[str, Any], kind: str) -> tuple[str, str]:
    keys = theme.get("edge_map", {}).get(kind, ["muted", "solid"])
    return theme.get(keys[0], theme["muted"]), keys[1]


def base_element(
    element_type: str,
    key: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    stroke: str = "#101828",
    background: str = "transparent",
    stroke_width: float = 2,
    stroke_style: str = "solid",
    opacity: int = 100,
    frame_id: str | None = None,
    link: str | None = None,
    roundness: dict[str, Any] | None = None,
    roughness: int = 0,
    custom_data: dict[str, Any] | None = None,
    group_ids: list[str] | None = None,
    locked: bool = False,
) -> dict[str, Any]:
    eid = stable_id(element_type[:3], key)
    element: dict[str, Any] = {
        "id": eid,
        "type": element_type,
        "x": round(float(x), 2),
        "y": round(float(y), 2),
        "width": round(float(width), 2),
        "height": round(float(height), 2),
        "angle": 0,
        "strokeColor": stroke,
        "backgroundColor": background,
        "fillStyle": "solid",
        "strokeWidth": stroke_width,
        "strokeStyle": stroke_style,
        "roughness": roughness,
        "opacity": opacity,
        "groupIds": group_ids or [],
        "frameId": frame_id,
        "roundness": roundness,
        "seed": stable_int(key + ":seed"),
        "version": 1,
        "versionNonce": stable_int(key + ":nonce"),
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": link,
        "locked": locked,
    }
    if custom_data:
        element["customData"] = custom_data
    return element


def text_element(
    key: str,
    x: float,
    y: float,
    value: str,
    *,
    font_size: int = 18,
    width: float | None = None,
    height: float | None = None,
    color: str = "#101828",
    align: str = "left",
    valign: str = "middle",
    frame_id: str | None = None,
    link: str | None = None,
    group_ids: list[str] | None = None,
    font_family: int = 2,
    opacity: int = 100,
    custom_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    measured_w, measured_h = estimate_text_box(value, font_size, int(width or 900))
    e = base_element(
        "text", key, x, y, float(width or measured_w), float(height or measured_h),
        stroke=color, background="transparent", stroke_width=1, opacity=opacity,
        frame_id=frame_id, link=link, roughness=0, group_ids=group_ids,
        custom_data=custom_data,
    )
    e.update({
        "fontSize": int(font_size),
        "fontFamily": int(font_family),
        "text": value,
        "textAlign": align,
        "verticalAlign": valign,
        "containerId": None,
        "originalText": value,
        "autoResize": False,
        "lineHeight": 1.25,
        "baseline": max(1, int(font_size * 1.1)),
    })
    return e


def rectangle(
    key: str, x: float, y: float, w: float, h: float, *, theme: dict[str, Any],
    stroke: str | None = None, background: str | None = None, stroke_width: float = 1.5,
    opacity: int = 100, frame_id: str | None = None, link: str | None = None,
    role: str | None = None, group_ids: list[str] | None = None, locked: bool = False,
    radius: bool = True,
) -> dict[str, Any]:
    meta = {"imCodeMap": {"role": role}} if role else None
    return base_element(
        "rectangle", key, x, y, w, h,
        stroke=stroke or theme["border"], background=background or theme["surface"],
        stroke_width=stroke_width, opacity=opacity, frame_id=frame_id, link=link,
        roundness={"type": 3} if radius else None, roughness=theme["roughness"],
        custom_data=meta, group_ids=group_ids, locked=locked,
    )


def ellipse(
    key: str, x: float, y: float, w: float, h: float, *, theme: dict[str, Any],
    stroke: str | None = None, background: str = "transparent", stroke_width: float = 2,
    opacity: int = 100, frame_id: str | None = None, link: str | None = None,
    role: str | None = None, group_ids: list[str] | None = None,
) -> dict[str, Any]:
    meta = {"imCodeMap": {"role": role}} if role else None
    return base_element(
        "ellipse", key, x, y, w, h, stroke=stroke or theme["ink"], background=background,
        stroke_width=stroke_width, opacity=opacity, frame_id=frame_id, link=link,
        roughness=theme["roughness"], custom_data=meta, group_ids=group_ids,
    )


def polyline(
    key: str,
    points: list[tuple[float, float]],
    *,
    theme: dict[str, Any],
    stroke: str,
    stroke_width: float = 2,
    stroke_style: str = "solid",
    frame_id: str | None = None,
    role: str | None = None,
    custom: dict[str, Any] | None = None,
    group_ids: list[str] | None = None,
    link: str | None = None,
    end_arrowhead: str | None = None,
    start_arrowhead: str | None = None,
    opacity: int = 100,
) -> dict[str, Any]:
    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_x = max(p[0] for p in points)
    max_y = max(p[1] for p in points)
    meta = dict(custom or {})
    if role:
        meta.setdefault("role", role)
    e = base_element(
        "line", key, min_x, min_y, max(1, max_x - min_x), max(1, max_y - min_y),
        stroke=stroke, background="transparent", stroke_width=stroke_width,
        stroke_style=stroke_style, opacity=opacity, frame_id=frame_id, link=link,
        roundness={"type": 2}, roughness=theme["roughness"],
        custom_data={"imCodeMap": meta} if meta else None, group_ids=group_ids,
    )
    e.update({
        "points": [[round(px - min_x, 2), round(py - min_y, 2)] for px, py in points],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": start_arrowhead,
        "endArrowhead": end_arrowhead,
        "elbowed": False,
    })
    return e


def shadow_element(key: str, x: float, y: float, w: float, h: float, *, theme: dict[str, Any], frame_id: str | None = None) -> dict[str, Any]:
    off = float(theme.get("shadow_offset", 6))
    return rectangle(
        key, x + off, y + off, w, h, theme=theme, stroke=theme["shadow"],
        background=theme["shadow"], stroke_width=0, opacity=int(theme.get("shadow_opacity", 8)),
        frame_id=frame_id, role="shadow", radius=True,
    )


def clean_node_label(value: str) -> str:
    return re.sub(r"^\s*\d+\s*[.)·:-]\s*", "", str(value or "")).strip()


def note_label(path: str) -> str:
    """Return a short, destination-specific navigation label.

    Earlier Atlas scenes collapsed every note below ``architecture/atlas`` into the
    same visible label, "Deep Atlas".  Four identical buttons with four different
    links are not navigation; they are a small usability prank.  Prefer the note's
    semantic collection before falling back to the generic Atlas label.
    """
    raw = str(path).strip("[]")
    stem = Path(raw).stem.replace("-", " ")
    lower = raw.lower()
    if "visual-index" in lower:
        return "그림 목차"
    if "/atlas/start-here" in lower:
        return "Atlas 시작"
    # Match collection indexes before the generic atlas index. The old substring
    # check treated ``/atlas/indexes/domains.md`` as ``/atlas/index.md``, creating
    # identical visible buttons that pointed to different destinations.
    if "/atlas/indexes/domains" in lower:
        return "도메인 목차"
    if "/atlas/indexes/streams" in lower:
        return "스트림 목차"
    if "/atlas/indexes/states-rules" in lower:
        return "상태·규칙 목차"
    if "/atlas/index.md" in lower or lower.endswith("/atlas/index"):
        return "Atlas 목차"
    if "start-here" in lower:
        return "시작 문서"
    if "/understanding/" in lower:
        return "질문 문서"
    if "/atlas/flows/" in lower:
        return clamp_text(stem.replace(" lifecycle", ""), 2, 20)
    if "/flows/" in lower:
        return "흐름 문서"
    if "/states/" in lower:
        state_name = stem.replace(" lifecycle", "").strip()
        state_names = {
            "mission": "Mission 상태",
            "workflow run": "Run 상태",
            "workflow step run": "Step 상태",
            "issue": "Issue 상태",
        }
        return state_names.get(state_name.lower(), clamp_text(f"{state_name} 상태", 2, 20))
    if "/rules/" in lower:
        return clamp_text(stem.removeprefix("rule "), 2, 20)
    if "/domains/" in lower:
        return clamp_text(stem, 2, 20)
    if "/actors/" in lower:
        return clamp_text(stem, 2, 20)
    if "/entities/" in lower:
        return clamp_text(stem, 2, 20)
    if "/codebases/" in lower:
        return clamp_text(stem, 2, 20)
    if "unknown" in lower:
        return "미확인 사항"
    if "/atlas" in lower:
        return "전체 지도"
    return clamp_text(stem, 3, 20)


def chip_elements(
    key: str,
    x: float,
    y: float,
    label: str,
    *,
    theme: dict[str, Any],
    color: str | None = None,
    background: str | None = None,
    link: str | None = None,
    frame_id: str | None = None,
    font_size: int = 12,
    min_width: float = 72,
    role: str = "chip",
) -> tuple[list[dict[str, Any]], float]:
    label = clamp_text(label, 4, 28)
    width = max(min_width, len(label) * font_size * 0.58 + 28)
    height = 30 if font_size <= 12 else 36
    color = color or theme["primary"]
    background = background or theme["primary_soft"]
    group = stable_id("grp", key)
    bg = rectangle(
        key + ":bg", x, y, width, height, theme=theme, stroke=color, background=background,
        stroke_width=1, frame_id=frame_id, link=link, role=role, group_ids=[group], radius=True,
    )
    txt = text_element(
        key + ":text", x + 10, y + 1, label, font_size=font_size, width=width - 20,
        height=height - 2, color=color, align="center", valign="middle", frame_id=frame_id,
        link=link, group_ids=[group], font_family=theme["font_family"],
        custom_data={"imCodeMap": {"role": role + "-text"}},
    )
    return [bg, txt], width


def icon_elements(
    kind: str,
    key: str,
    x: float,
    y: float,
    size: float,
    *,
    theme: dict[str, Any],
    stroke: str,
    frame_id: str | None,
    group_id: str,
    node_id: str | None = None,
    link: str | None = None,
) -> list[dict[str, Any]]:
    """Create a consistent native-vector icon in a square coordinate system."""
    kind = kind if kind in ICON_KINDS else "process"
    s = size / 32.0
    bx, by = x, y
    cx, cy = bx + 16 * s, by + 16 * s
    meta = {"role": "node-icon", "nodeId": node_id} if node_id else {"role": "stencil-icon", "icon": kind}

    def line(suffix: str, pts: Iterable[tuple[float, float]], arrow: str | None = None, width: float = 2.1) -> dict[str, Any]:
        return polyline(
            f"{key}:{suffix}", [(bx + px * s, by + py * s) for px, py in pts],
            theme=theme, stroke=stroke, stroke_width=width, frame_id=frame_id,
            custom=meta, group_ids=[group_id], link=link, end_arrowhead=arrow,
        )

    def ell(suffix: str, px: float, py: float, pw: float, ph: float, fill: str = "transparent") -> dict[str, Any]:
        e = base_element(
            "ellipse", f"{key}:{suffix}", bx + px * s, by + py * s, pw * s, ph * s,
            stroke=stroke, background=fill, stroke_width=2.1, frame_id=frame_id, link=link,
            roughness=theme["roughness"], custom_data={"imCodeMap": meta}, group_ids=[group_id],
        )
        return e

    def rect(suffix: str, px: float, py: float, pw: float, ph: float, fill: str = "transparent", radius: bool = True) -> dict[str, Any]:
        e = base_element(
            "rectangle", f"{key}:{suffix}", bx + px * s, by + py * s, pw * s, ph * s,
            stroke=stroke, background=fill, stroke_width=2.1, frame_id=frame_id, link=link,
            roundness={"type": 3} if radius else None, roughness=theme["roughness"],
            custom_data={"imCodeMap": meta}, group_ids=[group_id],
        )
        return e

    if kind in {"actor"}:
        return [ell("head", 12, 2, 8, 8), line("body", [(16, 10), (16, 22)]), line("arms", [(8, 15), (24, 15)]), line("legs", [(16, 22), (9, 30), (16, 22), (23, 30)])]
    if kind in {"start", "flow"}:
        return [line("play", [(9, 5), (9, 27), (25, 16), (9, 5)])]
    if kind in {"end"}:
        return [line("check", [(4, 17), (12, 25), (28, 7)], width=2.8)]
    if kind in {"decision", "question"}:
        return [ell("circle", 3, 3, 26, 26), line("q1", [(11, 11), (13, 8), (18, 8), (21, 11), (21, 14), (17, 17), (16, 20)]), ell("dot", 14.5, 24, 3, 3, stroke)]
    if kind in {"state-change"}:
        return [line("top", [(3, 9), (25, 9)], "arrow"), line("bottom", [(29, 23), (7, 23)], "arrow")]
    if kind in {"event"}:
        return [line("bolt", [(18, 1), (7, 17), (15, 17), (10, 31), (27, 12), (18, 12), (18, 1)], width=2.4)]
    if kind in {"wait"}:
        return [ell("clock", 3, 3, 26, 26), line("hands", [(16, 7), (16, 17), (23, 21)])]
    if kind in {"data"}:
        return [rect("row1", 3, 4, 26, 6), rect("row2", 3, 13, 26, 6), rect("row3", 3, 22, 26, 6)]
    if kind in {"storage"}:
        return [ell("top", 3, 3, 26, 8), rect("body", 3, 7, 26, 19, radius=False), ell("bottom", 3, 22, 26, 8), line("mid", [(3, 10), (3, 23), (29, 23), (29, 10)])]
    if kind in {"external"}:
        return [ell("globe", 3, 3, 26, 26), line("lat", [(4, 16), (28, 16)]), line("lon", [(16, 4), (10, 16), (16, 28), (22, 16), (16, 4)])]
    if kind in {"error", "risk", "unknown", "boundary"}:
        return [line("triangle", [(16, 2), (30, 29), (2, 29), (16, 2)]), line("bang", [(16, 10), (16, 20)], width=2.8), ell("dot", 14.5, 24, 3, 3, stroke)]
    if kind in {"compensation"}:
        return [line("undo", [(28, 8), (12, 8), (5, 16), (12, 24), (25, 24)], "arrow")]
    if kind in {"domain"}:
        return [rect("a", 2, 2, 12, 12), rect("b", 18, 2, 12, 12), rect("c", 2, 18, 12, 12), rect("d", 18, 18, 12, 12)]
    if kind in {"codebase"}:
        return [line("left", [(12, 5), (4, 16), (12, 27)]), line("right", [(20, 5), (28, 16), (20, 27)])]
    if kind in {"note", "atlas"}:
        return [rect("page", 5, 2, 22, 28), line("fold", [(20, 2), (27, 9), (20, 9), (20, 2)]), line("n1", [(9, 14), (23, 14)]), line("n2", [(9, 20), (23, 20)]), line("n3", [(9, 26), (19, 26)])]
    if kind in {"test"}:
        return [rect("box", 3, 3, 26, 26), line("check", [(8, 17), (14, 23), (25, 10)], width=2.6)]
    if kind in {"service", "api", "process"}:
        return [rect("body", 3, 5, 26, 22), ell("p1", 7, 11, 4, 4, stroke), line("l1", [(14, 13), (25, 13)]), ell("p2", 7, 19, 4, 4, stroke), line("l2", [(14, 21), (25, 21)])]
    if kind in {"queue"}:
        return [rect("q1", 2, 8, 7, 16), rect("q2", 12, 8, 7, 16), rect("q3", 22, 8, 7, 16), line("arrow", [(1, 4), (30, 4)], "arrow")]
    if kind in {"worker"}:
        return [ell("gear", 5, 5, 22, 22), ell("hub", 12, 12, 8, 8), line("spokes", [(16, 1), (16, 6), (16, 26), (16, 31), (1, 16), (6, 16), (26, 16), (31, 16)])]
    if kind in {"product"}:
        return [line("tag", [(4, 5), (20, 5), (29, 14), (18, 27), (4, 16), (4, 5)]), ell("hole", 9, 9, 4, 4)]
    if kind in {"order"}:
        return [rect("receipt", 6, 2, 20, 28), line("r1", [(10, 9), (22, 9)]), line("r2", [(10, 15), (22, 15)]), line("r3", [(10, 21), (19, 21)])]
    if kind in {"payment"}:
        return [rect("card", 2, 7, 28, 20), line("stripe", [(3, 13), (29, 13)]), line("chip", [(7, 18), (13, 18), (13, 23), (7, 23), (7, 18)])]
    if kind in {"shield"}:
        return [line("shield", [(16, 2), (28, 7), (27, 18), (22, 26), (16, 30), (10, 26), (5, 18), (4, 7), (16, 2)]), line("check", [(10, 16), (14, 20), (22, 11)])]
    if kind in {"search"}:
        return [ell("glass", 3, 3, 20, 20), line("handle", [(20, 20), (30, 30)], width=2.8)]
    if kind in {"browser"}:
        return [rect("window", 2, 4, 28, 24), line("bar", [(2, 10), (30, 10)]), ell("dot1", 5, 6, 2, 2, stroke), ell("dot2", 9, 6, 2, 2, stroke)]
    return [ell("hub", 11, 11, 10, 10), line("h", [(2, 16), (30, 16)]), line("v", [(16, 2), (16, 30)])]


def step_badge_elements(
    key: str, x: float, y: float, number: int | str, *, theme: dict[str, Any],
    frame_id: str | None, group_id: str, color: str | None = None,
) -> list[dict[str, Any]]:
    color = color or theme["primary"]
    circle = base_element(
        "ellipse", key + ":circle", x, y, 32, 32, stroke=color, background=color,
        stroke_width=1, frame_id=frame_id, roughness=theme["roughness"],
        custom_data={"imCodeMap": {"role": "step-badge"}}, group_ids=[group_id],
    )
    txt = text_element(
        key + ":text", x, y + 1, str(number), font_size=14, width=32, height=30,
        color="#FFFFFF", align="center", valign="middle", frame_id=frame_id,
        group_ids=[group_id], font_family=theme["font_family"],
        custom_data={"imCodeMap": {"role": "step-badge-text"}},
    )
    return [circle, txt]


def card_elements(
    node: dict[str, Any],
    box: tuple[float, float, float, float],
    *,
    theme: dict[str, Any],
    frame_id: str | None = None,
    compact: bool = False,
    focus_mode: bool = False,
    show_confidence: bool = False,
    icon_override: str | None = None,
    decision_as_card: bool = True,
) -> tuple[list[dict[str, Any]], str]:
    x, y, w, h = box
    kind = node.get("kind", "process")
    stroke, soft = semantic_style(theme, kind)
    group = stable_id("grp", "node:" + node["id"])
    link = node.get("details_link")
    shape_type = "rectangle"
    if not decision_as_card and kind == "decision":
        shape_type = "diamond"
    elif node.get("shape") in {"ellipse", "diamond", "rectangle"}:
        shape_type = node["shape"]

    elements: list[dict[str, Any]] = []
    if shape_type == "rectangle":
        elements.append(shadow_element("node-shadow:" + node["id"], x, y, w, h, theme=theme, frame_id=frame_id))
    custom = {
        "imCodeMap": {
            "role": "node", "nodeId": node["id"], "kind": kind,
            "sourceRefs": node.get("source_refs", []),
            "streamStepRef": node.get("stream_step_ref"),
            "confidence": node.get("confidence"),
        }
    }
    shape = base_element(
        shape_type, "node-shape:" + node["id"], x, y, w, h,
        stroke=stroke, background=soft if kind not in {"process", "codebase"} else theme["surface"],
        stroke_width=2.2 if kind in {"decision", "error", "risk", "compensation"} else 1.6,
        frame_id=frame_id, link=link,
        roundness={"type": 3} if shape_type == "rectangle" else None,
        roughness=theme["roughness"], custom_data=custom, group_ids=[group],
    )
    elements.append(shape)

    if shape_type == "rectangle":
        accent_h = 6 if not compact else 5
        elements.append(rectangle(
            "node-accent:" + node["id"], x, y, w, accent_h, theme=theme, stroke=stroke,
            background=stroke, stroke_width=0, frame_id=frame_id, role="node-accent",
            group_ids=[group], radius=True,
        ))

    icon_size = 34 if compact else 40
    tile_size = 44 if compact else 52
    tile_x = x + (15 if compact else 18)
    tile_y = y + (15 if compact else 18)
    if shape_type == "diamond":
        tile_x = x + w / 2 - tile_size / 2
        tile_y = y + 14
    tile = rectangle(
        "node-icon-tile:" + node["id"], tile_x, tile_y, tile_size, tile_size,
        theme=theme, stroke=soft, background=soft, stroke_width=0, frame_id=frame_id,
        link=link, role="node-icon-tile", group_ids=[group], radius=True,
    )
    elements.append(tile)
    icon_kind = icon_override or node.get("icon")
    if not icon_kind or icon_kind == "auto":
        icon_kind = kind
    elements.extend(icon_elements(
        str(icon_kind), "node-icon:" + node["id"], tile_x + (tile_size - icon_size) / 2,
        tile_y + (tile_size - icon_size) / 2, icon_size, theme=theme, stroke=stroke,
        frame_id=frame_id, group_id=group, node_id=node["id"], link=link,
    ))

    step = node.get("step_number")
    if step is not None:
        elements.extend(step_badge_elements(
            "node-step:" + node["id"], x - 13, y - 13, step, theme=theme,
            frame_id=frame_id, group_id=group, color=theme["primary"],
        ))

    if shape_type == "diamond":
        label = clean_node_label(clamp_text(node.get("label", node["id"]), 9, 68))
        summary = clamp_text(node.get("summary", ""), 13 if compact else 17, 110)
        value = wrap_text(label + ("\n" + summary if summary else ""), width=22, max_lines=5)
        txt = text_element(
            "node-text:" + node["id"], x + 24, y + 50, value,
            font_size=14 if compact else 15, width=w - 48, height=h - 68,
            color=theme["ink"], align="center", valign="middle", frame_id=frame_id,
            link=link, group_ids=[group], font_family=theme["font_family"],
            custom_data={"imCodeMap": {"role": "node-label", "nodeId": node["id"]}},
        )
        elements.append(txt)
        return elements, shape["id"]

    label = clean_node_label(clamp_text(node.get("label", node["id"]), 10, 78))
    summary = clamp_text(node.get("summary", ""), 18 if compact else 24, 150)
    title_x = tile_x + tile_size + (13 if compact else 16)
    title_y = y + (15 if compact else 18)
    title_w = w - (title_x - x) - 18
    title_h = 30 if compact else 34
    elements.append(text_element(
        "node-title:" + node["id"], title_x, title_y, wrap_text(label, 24 if compact else 30, 2),
        font_size=15 if compact else 17, width=title_w, height=title_h,
        color=theme["ink"], align="left", valign="middle", frame_id=frame_id,
        link=link, group_ids=[group], font_family=theme["font_family"],
        custom_data={"imCodeMap": {"role": "node-label", "nodeId": node["id"]}},
    ))

    if kind == "decision":
        chips, cw = chip_elements(
            "node-rule:" + node["id"], x + w - 84, y + h - 34, "조건",
            theme=theme, color=stroke, background=soft, frame_id=frame_id,
            font_size=11, min_width=62, role="semantic-chip",
        )
        for e in chips:
            e["groupIds"] = [group]
        elements.extend(chips)

    state = ""
    if node.get("state_before") or node.get("state_after"):
        state = f"{node.get('state_before', '?')} → {node.get('state_after', '?')}"
    body_lines = [summary] if summary else []
    if state:
        body_lines.append(state)
    if show_confidence and node.get("confidence") not in {None, "VERIFIED"}:
        body_lines.append(str(node.get("confidence")))
    body = wrap_text("\n".join(body_lines), 26 if compact else 23, 5 if compact else 6)
    body_y = y + (57 if compact else 68)
    body_h = h - (body_y - y) - (13 if compact else 16)
    if kind == "decision":
        body_h -= 22
    elements.append(text_element(
        "node-body:" + node["id"], x + (15 if compact else 18), body_y, body,
        font_size=12 if compact else 14, width=w - (30 if compact else 36), height=max(28, body_h),
        color=theme["muted"], align="left", valign="top", frame_id=frame_id,
        link=link, group_ids=[group], font_family=theme["font_family"],
        custom_data={"imCodeMap": {"role": "node-body", "nodeId": node["id"]}},
    ))
    return elements, shape["id"]


def header_elements(
    diagram: dict[str, Any], *, theme: dict[str, Any], width: float,
    profile_label: str, x: float = 56, y: float = 38,
) -> tuple[list[dict[str, Any]], float]:
    elements: list[dict[str, Any]] = []
    eyebrow, _ = chip_elements(
        "header-profile:" + diagram["id"], x, y, profile_label,
        theme=theme, color=theme["primary"], background=theme["primary_soft"],
        font_size=12, min_width=120, role="profile-chip",
    )
    elements.extend(eyebrow)
    elements.append(text_element(
        "diagram-title:" + diagram["id"], x, y + 48, diagram.get("title", diagram["id"]),
        font_size=36, width=min(980, width - 112), height=54, color=theme["ink"],
        align="left", valign="middle", font_family=theme["font_family"],
        custom_data={"imCodeMap": {"role": "diagram-title"}},
    ))
    elements.append(text_element(
        "diagram-purpose:" + diagram["id"], x, y + 105,
        wrap_text(clamp_text(diagram.get("purpose", ""), 34, 220), 90, 2),
        font_size=16, width=min(1040, width - 112), height=48, color=theme["muted"],
        align="left", valign="top", font_family=theme["font_family"],
        custom_data={"imCodeMap": {"role": "diagram-purpose"}},
    ))

    notes = list(diagram.get("navigation", {}).get("related_notes", []))[:4]
    if notes:
        button_y = y + 43
        x_cursor = width - 56
        rendered: list[tuple[list[dict[str, Any]], float]] = []
        for idx, note in enumerate(reversed(notes)):
            label = note_label(note)
            link = note if note.startswith("[[") else f"[[{note}]]"
            group, bw = chip_elements(
                f"header-nav:{diagram['id']}:{idx}", 0, button_y, label,
                theme=theme, color=theme["muted"], background=theme["surface"], link=link,
                font_size=12, min_width=104, role="navigation-button",
            )
            rendered.append((group, bw))
        for group, bw in rendered:
            x_cursor -= bw
            for e in group:
                e["x"] = round(e["x"] + x_cursor, 2)
            x_cursor -= 10
            elements.extend(group)
    return elements, y + 170


def arrow_elements(
    edge: dict[str, Any],
    source_shape: dict[str, Any],
    target_shape: dict[str, Any],
    points: list[tuple[float, float]],
    *,
    theme: dict[str, Any],
    frame_id: str | None = None,
    show_label: bool = True,
    label_position: tuple[float, float] | None = None,
) -> list[dict[str, Any]]:
    kind = edge.get("kind", "happy-path")
    color, default_style = edge_style(theme, kind)
    style = edge.get("style") or default_style
    key = "edge:" + edge["id"]
    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_x = max(p[0] for p in points)
    max_y = max(p[1] for p in points)
    arrow = base_element(
        "arrow", key, min_x, min_y, max(1, max_x - min_x), max(1, max_y - min_y),
        stroke=color, background="transparent", stroke_width=3 if kind in {"happy-path", "error", "compensation"} else 2.2,
        stroke_style=style, frame_id=frame_id, roundness={"type": 2}, roughness=theme["roughness"],
        custom_data={"imCodeMap": {
            "role": "edge", "edgeId": edge["id"], "kind": kind,
            "from": edge["from"], "to": edge["to"], "condition": edge.get("condition", ""),
            "confidence": edge.get("confidence"),
        }},
    )
    arrow.update({
        "points": [[round(px - min_x, 2), round(py - min_y, 2)] for px, py in points],
        "lastCommittedPoint": None,
        "startBinding": {"elementId": source_shape["id"], "focus": 0, "gap": 6},
        "endBinding": {"elementId": target_shape["id"], "focus": 0, "gap": 6},
        "startArrowhead": None,
        "endArrowhead": "arrow",
        "elbowed": False,
    })
    source_shape.setdefault("boundElements", []).append({"id": arrow["id"], "type": "arrow"})
    target_shape.setdefault("boundElements", []).append({"id": arrow["id"], "type": "arrow"})
    elements: list[dict[str, Any]] = [arrow]
    label_parts = [str(edge.get("label", "")).strip()]
    condition = str(edge.get("condition", "")).strip()
    if condition and condition.lower() not in {label_parts[0].lower() if label_parts[0] else "", "n/a", "none"}:
        label_parts.append(condition)
    label = " · ".join(x for x in label_parts if x)
    if show_label and label:
        lx, ly = label_position or points[len(points) // 2]
        pills, _ = chip_elements(
            "edge-label:" + edge["id"], lx - 42, ly - 16, clamp_text(label, 6, 34),
            theme=theme, color=color, background=theme["surface"], frame_id=frame_id,
            font_size=11, min_width=84, role="edge-label",
        )
        elements.extend(pills)
    return elements


def scene_root(diagram: dict[str, Any], elements: list[dict[str, Any]], *, theme: dict[str, Any], source: str = "im-code-map-v5.1") -> dict[str, Any]:
    return {
        "type": "excalidraw",
        "version": 2,
        "source": source,
        "elements": elements,
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
            "diagramId": diagram["id"],
            "diagramType": diagram["type"],
            "purpose": diagram.get("purpose", ""),
            "sourceRefs": diagram.get("source_refs", []),
            "nodeIds": [n["id"] for n in diagram.get("nodes", [])],
            "edgeIds": [e["id"] for e in diagram.get("edges", [])],
            "generated": True,
        },
    }
