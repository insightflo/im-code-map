#!/usr/bin/env python3
"""Generate polished, deterministic Excalidraw scenes from im-code-map visual models.

v5.1 separates presentation from evidence. Focus diagrams use a narrative storyboard;
Atlas diagrams use system-design boundaries, swimlanes, and compact semantic cards.
Only native Excalidraw primitives are emitted, so diagrams remain editable in Obsidian.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from excalidraw_design_system import (
    arrow_elements,
    card_elements,
    chip_elements,
    header_elements,
    load_design,
    rectangle,
    scene_root,
    semantic_style,
    shadow_element,
    text_element,
)
from im_code_map_common import clamp_text, read_json, stable_id, wrap_text, write_json


def node_map(diagram: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {n["id"]: n for n in diagram.get("nodes", [])}


def element_role(element: dict[str, Any]) -> str:
    return ((element.get("customData") or {}).get("imCodeMap") or {}).get("role", "")


def shape_from_group(elements: Iterable[dict[str, Any]]) -> dict[str, Any]:
    for element in elements:
        if element_role(element) == "node":
            return element
    raise ValueError("node group has no semantic shape")


def center(box: tuple[float, float, float, float]) -> tuple[float, float]:
    x, y, w, h = box
    return x + w / 2, y + h / 2


def anchor(box: tuple[float, float, float, float], side: str) -> tuple[float, float]:
    x, y, w, h = box
    return {
        "left": (x, y + h / 2),
        "right": (x + w, y + h / 2),
        "top": (x + w / 2, y),
        "bottom": (x + w / 2, y + h),
    }[side]


def split_edge_parts(parts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    for element in parts:
        if element_role(element) == "edge":
            lines.append(element)
        else:
            labels.append(element)
    return lines, labels


def panel_elements(
    key: str,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str,
    *,
    theme: dict[str, Any],
    accent: str | None = None,
    index: int | None = None,
    role: str = "section-panel",
) -> list[dict[str, Any]]:
    accent = accent or theme["primary"]
    elements: list[dict[str, Any]] = [
        shadow_element(key + ":shadow", x, y, w, h, theme=theme),
        rectangle(
            key + ":bg", x, y, w, h, theme=theme, stroke=theme["border"],
            background=theme["surface"], stroke_width=1.4, role=role,
        ),
        rectangle(
            key + ":accent", x, y, 8, h, theme=theme, stroke=accent,
            background=accent, stroke_width=0, role=role + "-accent",
        ),
    ]
    tx = x + 28
    if index is not None:
        chips, width = chip_elements(
            key + ":index", tx, y + 22, f"PHASE {index}", theme=theme,
            color=accent, background=theme["surface_alt"], font_size=11,
            min_width=88, role="phase-chip",
        )
        elements.extend(chips)
        tx += width + 16
    elements.extend([
        text_element(
            key + ":title", tx, y + 18, title, font_size=21, width=w - (tx - x) - 24,
            height=34, color=theme["ink"], align="left", valign="middle",
            font_family=theme["font_family"], custom_data={"imCodeMap": {"role": role + "-title"}},
        ),
        text_element(
            key + ":subtitle", x + 28, y + 58, wrap_text(clamp_text(subtitle, 20, 150), 82, 2),
            font_size=13, width=w - 56, height=42, color=theme["muted"], align="left",
            valign="top", font_family=theme["font_family"],
            custom_data={"imCodeMap": {"role": role + "-subtitle"}},
        ),
    ])
    return elements


def overview_icon(node_id: str, kind: str) -> str:
    if node_id == "overview-question":
        return "question"
    if node_id == "overview-flow":
        return "flow"
    if node_id == "overview-boundary":
        return "boundary"
    if node_id == "overview-atlas":
        return "atlas"
    return kind


def render_human_overview(diagram: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    width = 1900.0
    bg: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    header, content_y = header_elements(diagram, theme=theme, width=width, profile_label="FOCUS · 3분 개요")
    bg.extend(header)

    guide_y = content_y + 4
    bg.extend(panel_elements(
        "overview-story", 48, guide_y, width - 96, 322,
        "질문에서 시작해 필요한 만큼만 깊어집니다",
        "전체 코드를 암기하는 대신, 한 가지 사용자 행동과 현재 근거의 경계를 따라갑니다.",
        theme=theme, accent=theme["primary"], role="story-panel",
    ))

    nodes = sorted(diagram.get("nodes", []), key=lambda n: int(n.get("step_number", n.get("order", 0))))
    card_w, card_h, gap = 320.0, 174.0, 34.0
    start_x = 92.0
    card_y = guide_y + 116
    boxes: dict[str, tuple[float, float, float, float]] = {}
    shapes: dict[str, dict[str, Any]] = {}
    for idx, node in enumerate(nodes):
        box = (start_x + idx * (card_w + gap), card_y, card_w, card_h)
        boxes[node["id"]] = box
        group, _ = card_elements(
            node, box, theme=theme, compact=False, focus_mode=True,
            icon_override=overview_icon(node["id"], node.get("kind", "process")),
            decision_as_card=True,
        )
        shapes[node["id"]] = shape_from_group(group)
        cards.extend(group)

    for edge in sorted(diagram.get("edges", []), key=lambda e: int(e.get("sequence", 0))):
        sb, tb = boxes[edge["from"]], boxes[edge["to"]]
        sx, sy = anchor(sb, "right")
        tx, ty = anchor(tb, "left")
        parts = arrow_elements(edge, shapes[edge["from"]], shapes[edge["to"]], [(sx + 6, sy), (tx - 6, ty)], theme=theme, show_label=False)
        line, lab = split_edge_parts(parts)
        edges.extend(line)
        labels.extend(lab)

    footer_y = guide_y + 350
    unknowns = diagram.get("reader_contract", {}).get("required_unknowns", [])
    does_not = diagram.get("reader_contract", {}).get("does_not_answer", [])
    bg.extend(panel_elements(
        "overview-boundary-note", 48, footer_y, 900, 152,
        "현재 확인이 필요한 것",
        " · ".join(unknowns) if unknowns else "현재 흐름을 막는 미확인 사항 없음",
        theme=theme, accent=theme["danger"], role="boundary-panel",
    ))
    bg.extend(panel_elements(
        "overview-scope-note", 980, footer_y, 872, 152,
        "이번 지도에서 다루지 않는 것",
        " · ".join(does_not[:4]) if does_not else "명시적으로 제외된 범위 없음",
        theme=theme, accent=theme["subtle"], role="scope-panel",
    ))
    return scene_root(diagram, [*bg, *edges, *cards, *labels], theme=theme)


def phase_title(index: int) -> tuple[str, str]:
    return {
        1: ("주문 가능성 확인", "회원과 상품이 지금 주문 가능한지 확인하고 주문을 접수합니다."),
        2: ("재고와 결제 준비", "재고를 예약한 뒤 외부 결제 승인 요청을 시작합니다."),
        3: ("승인과 완료", "결제 결과를 반영하고 후속 처리 이벤트와 주문 번호를 반환합니다."),
    }.get(index, (f"업무 단계 {index}", "관련 처리와 판단을 순서대로 읽습니다."))


def render_focus_flow(diagram: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    width = 1820.0
    bg: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    header, content_y = header_elements(diagram, theme=theme, width=width, profile_label="FOCUS · 중심 업무 흐름")
    bg.extend(header)

    nodes = node_map(diagram)
    primary_ids = diagram.get("reader_contract", {}).get("primary_story_node_ids", [])
    primary = [nodes[nid] for nid in primary_ids if nid in nodes]
    by_phase: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in primary:
        by_phase[node.get("lane", "phase-1")].append(node)
    lane_order = [lane["id"] for lane in diagram.get("lanes", []) if lane.get("kind") == "phase"]

    panel_x, panel_w, panel_h = 48.0, width - 96, 270.0
    card_w, card_h, card_gap = 354.0, 138.0, 34.0
    card_start_x = panel_x + 130
    boxes: dict[str, tuple[float, float, float, float]] = {}
    shapes: dict[str, dict[str, Any]] = {}
    phase_y: dict[str, float] = {}

    for phase_index, lane_id in enumerate(lane_order, start=1):
        y = content_y + (phase_index - 1) * 300
        phase_y[lane_id] = y
        title, subtitle = phase_title(phase_index)
        accent = [theme["primary"], theme["purple"], theme["info"]][min(phase_index - 1, 2)]
        bg.extend(panel_elements(
            f"focus-phase:{phase_index}", panel_x, y, panel_w, panel_h,
            title, subtitle, theme=theme, accent=accent, index=phase_index, role="phase-panel",
        ))
        phase_nodes = sorted(by_phase.get(lane_id, []), key=lambda n: int(n.get("step_number", n.get("order", 0))))
        for local_index, node in enumerate(phase_nodes):
            box = (card_start_x + local_index * (card_w + card_gap), y + 112, card_w, card_h)
            boxes[node["id"]] = box
            icon = node.get("kind", "process")
            if node.get("step_number") == 1:
                icon = "order"
            elif node.get("step_number") == 3:
                icon = "product"
            elif node.get("step_number") == 8:
                icon = "payment"
            group, _ = card_elements(
                node, box, theme=theme, compact=True, focus_mode=True,
                icon_override=icon, decision_as_card=True,
            )
            shapes[node["id"]] = shape_from_group(group)
            cards.extend(group)

    primary_edges = [e for e in diagram.get("edges", []) if e.get("from") in boxes and e.get("to") in boxes]
    for edge in sorted(primary_edges, key=lambda e: int(e.get("sequence", 0))):
        sb, tb = boxes[edge["from"]], boxes[edge["to"]]
        same_row = abs(sb[1] - tb[1]) < 10
        if same_row:
            sx, sy = anchor(sb, "right")
            tx, ty = anchor(tb, "left")
            points = [(sx + 5, sy), (tx - 5, ty)]
            label_pos = ((sx + tx) / 2, sy)
        else:
            # All phases read left-to-right. The connector uses the right gutter and the inter-phase gap,
            # avoiding the old snake layout that asked readers to reverse direction every four nodes.
            sx, sy = anchor(sb, "right")
            tx, ty = anchor(tb, "left")
            gutter_x = panel_x + panel_w - 20
            middle_y = phase_y.get(nodes[edge["to"]].get("lane"), tb[1]) - 14
            points = [(sx + 5, sy), (gutter_x, sy), (gutter_x, middle_y), (tx - 28, middle_y), (tx - 28, ty), (tx - 5, ty)]
            label_pos = (gutter_x - 74, middle_y)
        parts = arrow_elements(
            edge, shapes[edge["from"]], shapes[edge["to"]], points,
            theme=theme, show_label=bool(edge.get("label") or edge.get("condition")), label_position=label_pos,
        )
        line, lab = split_edge_parts(parts)
        edges.extend(line)
        labels.extend(lab)

    context_nodes = [n for n in diagram.get("nodes", []) if n.get("role") in {"failure-summary", "unknown", "atlas-link"}]
    context_y = content_y + len(lane_order) * 300 + 12
    bg.append(text_element(
        "focus-context-heading:" + diagram["id"], panel_x, context_y,
        "흐름이 멈추는 이유와 다음 탐색", font_size=24, width=900, height=40,
        color=theme["ink"], align="left", valign="middle", font_family=theme["font_family"],
        custom_data={"imCodeMap": {"role": "context-heading"}},
    ))
    context_w, context_h, context_gap = 548.0, 170.0, 34.0
    for idx, node in enumerate(context_nodes[:3]):
        box = (panel_x + idx * (context_w + context_gap), context_y + 58, context_w, context_h)
        group, _ = card_elements(
            node, box, theme=theme, compact=False, focus_mode=True,
            icon_override={"failure-summary": "risk", "unknown": "unknown", "atlas-link": "atlas"}.get(node.get("role"), node.get("kind")),
            decision_as_card=True,
        )
        cards.extend(group)

    does_not = diagram.get("reader_contract", {}).get("does_not_answer", [])
    footer_y = context_y + 250
    bg.extend(panel_elements(
        "focus-scope:" + diagram["id"], panel_x, footer_y, panel_w, 122,
        "이 그림이 답하지 않는 것",
        " · ".join(does_not[:6]) if does_not else "현재 명시된 제외 범위 없음",
        theme=theme, accent=theme["subtle"], role="scope-panel",
    ))
    return scene_root(diagram, [*bg, *edges, *cards, *labels], theme=theme)


def atlas_lane_panel(
    key: str, x: float, y: float, w: float, h: float, label: str,
    *, theme: dict[str, Any], index: int,
) -> list[dict[str, Any]]:
    colors = [theme["blue"], theme["purple"], theme["info"], theme["warning"], theme["pink"], theme["success"]]
    accent = colors[index % len(colors)]
    return [
        rectangle(key + ":bg", x, y, w, h, theme=theme, stroke=theme["border"], background=theme["surface_alt"], stroke_width=1, role="lane-panel"),
        rectangle(key + ":bar", x, y, 10, h, theme=theme, stroke=accent, background=accent, stroke_width=0, role="lane-accent"),
        text_element(key + ":label", x + 20, y + 10, label, font_size=14, width=190, height=34, color=theme["ink"], align="left", valign="middle", font_family=theme["font_family"], custom_data={"imCodeMap": {"role": "lane-label"}}),
    ]


def generic_atlas_layout(diagram: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    header_width = 2200.0
    bg: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []

    # Frame groups are vertically stacked. Inside each frame, lane bands explain ownership,
    # while order drives the horizontal runtime sequence.
    frame_defs = {f["id"]: f for f in diagram.get("frames", [])}
    nodes_by_frame: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in diagram.get("nodes", []):
        nodes_by_frame[node.get("frame", "default")].append(node)
    ordered_frames = [f["id"] for f in sorted(diagram.get("frames", []), key=lambda f: int(f.get("order", 0)))] or list(nodes_by_frame)

    # Compute content width from the widest frame before drawing the header.
    widest = 0
    for frame_id in ordered_frames:
        orders = sorted({int(n.get("order", 0)) for n in nodes_by_frame.get(frame_id, [])})
        widest = max(widest, len(orders))
    content_w = max(1740.0, 280.0 + widest * 270.0)
    width = max(header_width, content_w + 96)
    header, content_y = header_elements(diagram, theme=theme, width=width, profile_label="DEEP ATLAS · 검증 가능한 상세")
    bg.extend(header)

    lanes = {lane["id"]: lane for lane in diagram.get("lanes", [])}
    boxes: dict[str, tuple[float, float, float, float]] = {}
    shapes: dict[str, dict[str, Any]] = {}
    cursor_y = content_y

    for frame_index, frame_id in enumerate(ordered_frames):
        frame_nodes = nodes_by_frame.get(frame_id, [])
        if not frame_nodes:
            continue
        lane_ids: list[str] = []
        for lane in diagram.get("lanes", []):
            if any(n.get("lane") == lane["id"] for n in frame_nodes):
                lane_ids.append(lane["id"])
        if not lane_ids:
            lane_ids = ["default"]
        lane_h = 178.0
        panel_h = 106.0 + len(lane_ids) * lane_h + 34
        frame = frame_defs.get(frame_id, {"label": frame_id, "purpose": ""})
        accent = [theme["primary"], theme["purple"], theme["info"], theme["warning"]][frame_index % 4]
        bg.extend(panel_elements(
            f"atlas-frame:{frame_id}", 48, cursor_y, width - 96, panel_h,
            frame.get("label", frame_id), frame.get("purpose", ""),
            theme=theme, accent=accent, index=frame_index + 1, role="atlas-frame",
        ))
        lane_x = 78.0
        node_start_x = 312.0
        order_values = sorted({int(n.get("order", 0)) for n in frame_nodes})
        order_rank = {value: idx for idx, value in enumerate(order_values)}
        for lane_index, lane_id in enumerate(lane_ids):
            ly = cursor_y + 100 + lane_index * lane_h
            lane_label = lanes.get(lane_id, {}).get("label") or lanes.get(lane_id, {}).get("title") or lane_id.replace("lane-", "").replace("-", " ").title()
            bg.extend(atlas_lane_panel(f"atlas-lane:{frame_id}:{lane_id}", lane_x, ly, width - 156, lane_h - 14, lane_label, theme=theme, index=lane_index))
            lane_nodes = [n for n in frame_nodes if n.get("lane") == lane_id] if lane_id != "default" else frame_nodes
            for node in lane_nodes:
                rank = order_rank[int(node.get("order", 0))]
                compact = True
                is_decision = node.get("kind") == "decision"
                w, h = (238.0, 146.0) if is_decision else (238.0, 126.0)
                x = node_start_x + rank * 270.0
                y = ly + (lane_h - 14 - h) / 2
                box = (x, y, w, h)
                boxes[node["id"]] = box
                group, _ = card_elements(
                    node, box, theme=theme, compact=compact, focus_mode=False,
                    decision_as_card=False, show_confidence=True,
                )
                shapes[node["id"]] = shape_from_group(group)
                cards.extend(group)
        cursor_y += panel_h + 42

    # Route by relative geometry. Orthogonal paths keep ownership bands readable.
    for edge in sorted(diagram.get("edges", []), key=lambda e: int(e.get("sequence", 0))):
        if edge.get("from") not in boxes or edge.get("to") not in boxes:
            continue
        sb, tb = boxes[edge["from"]], boxes[edge["to"]]
        scx, scy = center(sb)
        tcx, tcy = center(tb)
        if tcx > scx + 80:
            sx, sy = anchor(sb, "right")
            tx, ty = anchor(tb, "left")
            mid_x = (sx + tx) / 2
            points = [(sx + 5, sy), (mid_x, sy), (mid_x, ty), (tx - 5, ty)]
            label_pos = (mid_x, (sy + ty) / 2)
        elif abs(tcx - scx) <= 80 and tcy > scy:
            sx, sy = anchor(sb, "bottom")
            tx, ty = anchor(tb, "top")
            points = [(sx, sy + 5), (tx, ty - 5)]
            label_pos = ((sx + tx) / 2, (sy + ty) / 2)
        else:
            # Backward/terminal branches use a shallow outer elbow instead of crossing the source card.
            side_x = max(sb[0] + sb[2], tb[0] + tb[2]) + 42
            sx, sy = anchor(sb, "right")
            tx, ty = anchor(tb, "right")
            points = [(sx + 5, sy), (side_x, sy), (side_x, ty), (tx + 5, ty)]
            label_pos = (side_x, (sy + ty) / 2)
        parts = arrow_elements(
            edge, shapes[edge["from"]], shapes[edge["to"]], points,
            theme=theme, show_label=True, label_position=label_pos,
        )
        line, lab = split_edge_parts(parts)
        edges.extend(line)
        labels.extend(lab)

    return scene_root(diagram, [*bg, *edges, *cards, *labels], theme=theme)


def render_domain_overview(diagram: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    width = 1840.0
    bg: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    header, content_y = header_elements(diagram, theme=theme, width=width, profile_label="DEEP ATLAS · 도메인 경계")
    bg.extend(header)
    bg.extend(panel_elements(
        "domain-boundary", 48, content_y, width - 96, 760,
        "업무 소유권과 계약", "Ordering이 중심 조정자이며 각 도메인은 명시된 계약으로만 협력합니다.",
        theme=theme, accent=theme["primary"], role="domain-boundary",
    ))

    nodes = node_map(diagram)
    positions = {
        "d-order": (700.0, content_y + 270, 360.0, 190.0),
        "d-member": (110.0, content_y + 130, 330.0, 160.0),
        "d-catalog": (110.0, content_y + 470, 330.0, 160.0),
        "d-inventory": (1400.0, content_y + 120, 330.0, 160.0),
        "d-payment": (1400.0, content_y + 470, 330.0, 160.0),
        "d-worker": (720.0, content_y + 590, 320.0, 150.0),
    }
    boxes: dict[str, tuple[float, float, float, float]] = {}
    shapes: dict[str, dict[str, Any]] = {}
    fallback_x, fallback_y = 520.0, content_y + 110
    for idx, node in enumerate(diagram.get("nodes", [])):
        box = positions.get(node["id"], (fallback_x + (idx % 3) * 390, fallback_y + (idx // 3) * 220, 340.0, 160.0))
        boxes[node["id"]] = box
        icon = "worker" if node.get("kind") == "external" else "domain"
        group, _ = card_elements(node, box, theme=theme, compact=False, icon_override=icon, decision_as_card=True)
        shapes[node["id"]] = shape_from_group(group)
        cards.extend(group)

    for edge in sorted(diagram.get("edges", []), key=lambda e: int(e.get("sequence", 0))):
        sb, tb = boxes[edge["from"]], boxes[edge["to"]]
        scx, scy = center(sb)
        tcx, tcy = center(tb)
        if abs(tcx - scx) > abs(tcy - scy):
            s_side = "right" if tcx > scx else "left"
            t_side = "left" if tcx > scx else "right"
        else:
            s_side = "bottom" if tcy > scy else "top"
            t_side = "top" if tcy > scy else "bottom"
        sx, sy = anchor(sb, s_side)
        tx, ty = anchor(tb, t_side)
        mid = ((sx + tx) / 2, (sy + ty) / 2)
        points = [(sx, sy), (mid[0], sy), (mid[0], ty), (tx, ty)] if s_side in {"left", "right"} else [(sx, sy), (sx, mid[1]), (tx, mid[1]), (tx, ty)]
        parts = arrow_elements(edge, shapes[edge["from"]], shapes[edge["to"]], points, theme=theme, show_label=True, label_position=mid)
        line, lab = split_edge_parts(parts)
        edges.extend(line)
        labels.extend(lab)
    return scene_root(diagram, [*bg, *edges, *cards, *labels], theme=theme)


def render_diagram(diagram: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    dtype = diagram.get("type")
    if dtype == "human-overview":
        return render_human_overview(diagram, theme)
    if dtype == "focus-flow":
        return render_focus_flow(diagram, theme)
    if diagram.get("id") == "domain-commerce-overview" or dtype == "domain-overview":
        return render_domain_overview(diagram, theme)
    return generic_atlas_layout(diagram, theme)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visual_model", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--diagram", action="append", dest="diagram_ids")
    parser.add_argument("--theme", choices=["clean", "whiteboard"], default="clean")
    args = parser.parse_args()

    model = read_json(args.visual_model)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    selected = set(args.diagram_ids or [])
    theme = load_design(args.theme)
    count = 0
    for diagram in model.get("diagrams", []):
        if selected and diagram["id"] not in selected:
            continue
        scene = render_diagram(diagram, theme)
        path = args.output_dir / f"{diagram['id']}.excalidraw"
        write_json(path, scene)
        print(f"WROTE {path}")
        count += 1
    if not count:
        print("WARN: no diagrams selected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
