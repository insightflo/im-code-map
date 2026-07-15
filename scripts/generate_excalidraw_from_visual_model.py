#!/usr/bin/env python3
"""Generate polished, deterministic Excalidraw scenes from im-code-map visual models.

v5.1 separates presentation from evidence. Focus diagrams use a narrative storyboard;
Atlas diagrams use system-design boundaries, swimlanes, and compact semantic cards.
Only native Excalidraw primitives are emitted, so diagrams remain editable in Obsidian.
"""
from __future__ import annotations

import argparse
import re
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
            key + ":accent", x, y, 4, h, theme=theme, stroke=accent,
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
    card_w, card_h, gap = 220.0, 122.0, 34.0
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


def phase_title(lane: dict[str, Any], phase_nodes: list[dict[str, Any]], index: int) -> tuple[str, str]:
    """Derive a phase heading from the current Focus model, never from a demo domain.

    v5.1 accidentally baked the commerce example's 주문/재고/결제 headings into every
    generated Focus diagram.  The visual layer must consume the semantic lane and node
    labels supplied by the model instead of inventing domain language.
    """
    raw = str(lane.get("label") or "").strip()
    title = re.sub(r"^\s*(?:Phase\s+\d+|\d+단계)\s*[·:.-]?\s*", "", raw, flags=re.IGNORECASE).strip()
    labels = [re.sub(r"^\s*\d+\.\s*", "", str(node.get("label") or "")).strip() for node in phase_nodes]
    first = labels[0] if labels else ""
    last = labels[-1] if labels else ""
    if not title:
        title = first if first == last and first else (f"{first} → {last}" if first and last else f"업무 단계 {index}")
    korean = bool(re.search(r"[가-힣]", title + first + last))
    if first and last and first != last:
        subtitle = f"{first}부터 {last}까지 왼쪽에서 오른쪽으로 읽습니다." if korean else f"Read left to right from {first} through {last}."
    elif first:
        subtitle = f"{first} 처리와 판단을 확인합니다." if korean else f"Inspect the processing and decisions around {first}."
    else:
        subtitle = "관련 처리와 판단을 순서대로 읽습니다." if korean else "Read the related processing and decisions in order."
    return title, subtitle


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
    card_w, card_h, card_gap = 220.0, 138.0, 34.0
    card_start_x = panel_x + 130
    boxes: dict[str, tuple[float, float, float, float]] = {}
    shapes: dict[str, dict[str, Any]] = {}
    phase_y: dict[str, float] = {}

    phase_lane_by_id = {lane["id"]: lane for lane in diagram.get("lanes", []) if lane.get("kind") == "phase"}
    for phase_index, lane_id in enumerate(lane_order, start=1):
        y = content_y + (phase_index - 1) * 300
        phase_y[lane_id] = y
        phase_nodes = sorted(by_phase.get(lane_id, []), key=lambda n: int(n.get("step_number", n.get("order", 0))))
        title, subtitle = phase_title(phase_lane_by_id.get(lane_id, {}), phase_nodes, phase_index)
        accent = [theme["primary"], theme["purple"], theme["info"]][min(phase_index - 1, 2)]
        bg.extend(panel_elements(
            f"focus-phase:{phase_index}", panel_x, y, panel_w, panel_h,
            title, subtitle, theme=theme, accent=accent, index=phase_index, role="phase-panel",
        ))
        for local_index, node in enumerate(phase_nodes):
            box = (card_start_x + local_index * (card_w + card_gap), y + 112, card_w, card_h)
            boxes[node["id"]] = box
            icon = node.get("icon")
            if not icon or icon == "auto":
                icon = node.get("kind", "process")
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
    context_w, context_h, context_gap = 548.0, 218.0, 34.0
    for idx, node in enumerate(context_nodes[:3]):
        box = (panel_x + idx * (context_w + context_gap), context_y + 58, context_w, context_h)
        group, _ = card_elements(
            node, box, theme=theme, compact=False, focus_mode=True,
            icon_override={"failure-summary": "risk", "unknown": "unknown", "atlas-link": "atlas"}.get(node.get("role"), node.get("kind")),
            decision_as_card=True,
        )
        cards.extend(group)

    does_not = diagram.get("reader_contract", {}).get("does_not_answer", [])
    footer_y = context_y + 298
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



def state_primary_path(
    frame_nodes: list[dict[str, Any]],
    frame_edges: list[dict[str, Any]],
) -> list[str]:
    """Choose the normal lifecycle spine without pretending branch states are sequential.

    State diagrams used to place every state on one row by ``order``.  A transition such
    as ``active -> completed`` then ran behind a ``paused`` card, making the picture look
    like ``active -> paused -> completed``.  This helper finds the most plausible
    start-to-success path and moves all alternate/error/cancel states to a branch row.
    No transition is invented; the choice only controls layout.
    """
    nodes = {node["id"]: node for node in frame_nodes}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in frame_edges:
        src, dst = edge.get("from"), edge.get("to")
        if src in nodes and dst in nodes and src != dst:
            outgoing[src].append(dst)

    order = {nid: int(node.get("order", idx)) for idx, (nid, node) in enumerate(nodes.items())}
    starts = sorted(
        [nid for nid, node in nodes.items() if node.get("kind") == "start"],
        key=lambda nid: order[nid],
    )
    if not starts and nodes:
        starts = [min(nodes, key=lambda nid: order[nid])]

    branch_kinds = {"error", "compensation", "wait", "risk"}

    def path_score(path: list[str]) -> tuple[int, int, int, int]:
        last_kind = str(nodes[path[-1]].get("kind", "")) if path else ""
        success = 1 if last_kind == "end" else 0
        branch_penalty = sum(1 for nid in path if nodes[nid].get("kind") in branch_kinds)
        forwardness = sum(
            1 for left, right in zip(path, path[1:]) if order.get(right, 0) > order.get(left, 0)
        )
        return (success, len(path), forwardness, -branch_penalty)

    def best_from(nid: str, seen: frozenset[str]) -> list[str]:
        candidates: list[list[str]] = [[nid]]
        for target in sorted(outgoing.get(nid, []), key=lambda item: order.get(item, 0)):
            if target in seen:
                continue
            candidates.append([nid] + best_from(target, seen | {target}))
        return max(candidates, key=path_score)

    paths = [best_from(start, frozenset({start})) for start in starts]
    return max(paths, key=path_score) if paths else []


def render_state_machine(diagram: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    """Render lifecycle spines on the top row and alternative outcomes below.

    This preserves the actual graph semantics while keeping long guards readable.  It is
    deliberately wider than a compact flowchart because Excalidraw can zoom; semantic
    falsehood is not an acceptable space-saving technique.
    """
    bg: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []

    frame_defs = {f["id"]: f for f in diagram.get("frames", [])}
    nodes_by_frame: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in diagram.get("nodes", []):
        nodes_by_frame[node.get("frame", "default")].append(node)
    ordered_frames = [
        frame["id"]
        for frame in sorted(diagram.get("frames", []), key=lambda item: int(item.get("order", 0)))
    ] or list(nodes_by_frame)

    max_columns = max(
        (len({int(node.get("order", 0)) for node in nodes_by_frame.get(frame_id, [])}) for frame_id in ordered_frames),
        default=1,
    )
    column_step = 470.0
    node_start_x = 318.0
    card_w, card_h = 220.0, 126.0
    width = max(2200.0, node_start_x + max(0, max_columns - 1) * column_step + card_w + 110.0)
    header, content_y = header_elements(
        diagram, theme=theme, width=width, profile_label="DEEP ATLAS · 상태 분기"
    )
    bg.extend(header)

    lanes = {lane["id"]: lane for lane in diagram.get("lanes", [])}
    boxes: dict[str, tuple[float, float, float, float]] = {}
    shapes: dict[str, dict[str, Any]] = {}
    primary_by_frame: dict[str, set[str]] = {}
    cursor_y = content_y

    panel_h = 482.0
    lane_h = 342.0
    for frame_index, frame_id in enumerate(ordered_frames):
        frame_nodes = sorted(nodes_by_frame.get(frame_id, []), key=lambda node: int(node.get("order", 0)))
        if not frame_nodes:
            continue
        frame_edges = [
            edge for edge in diagram.get("edges", [])
            if edge.get("from") in {node["id"] for node in frame_nodes}
            and edge.get("to") in {node["id"] for node in frame_nodes}
        ]
        primary = set(state_primary_path(frame_nodes, frame_edges))
        primary_by_frame[frame_id] = primary

        frame = frame_defs.get(frame_id, {"label": frame_id, "purpose": ""})
        accent = [theme["primary"], theme["purple"], theme["info"], theme["warning"]][frame_index % 4]
        bg.extend(panel_elements(
            f"state-frame:{frame_id}", 48, cursor_y, width - 96, panel_h,
            frame.get("label", frame_id), frame.get("purpose", ""),
            theme=theme, accent=accent, index=frame_index + 1, role="state-frame",
        ))

        lane_id = next((node.get("lane") for node in frame_nodes if node.get("lane")), "default")
        lane_label = lanes.get(lane_id, {}).get("label") or frame.get("label", frame_id)
        lane_x, lane_y = 78.0, cursor_y + 100.0
        bg.extend(atlas_lane_panel(
            f"state-lane:{frame_id}:{lane_id}", lane_x, lane_y, width - 156, lane_h,
            lane_label, theme=theme, index=frame_index,
        ))

        main_y = lane_y + 54.0
        branch_y = lane_y + 216.0
        bg.extend([
            text_element(
                f"state-row-main:{frame_id}", lane_x + 22, main_y + 38,
                "주요 진행", font_size=13, width=180, height=30, color=theme["muted"],
                align="left", valign="middle", font_family=theme["font_family"],
                custom_data={"imCodeMap": {"role": "state-row-label"}},
            ),
            text_element(
                f"state-row-branch:{frame_id}", lane_x + 22, branch_y + 38,
                "분기·중단·별도 상태", font_size=13, width=190, height=30, color=theme["muted"],
                align="left", valign="middle", font_family=theme["font_family"],
                custom_data={"imCodeMap": {"role": "state-row-label"}},
            ),
        ])

        order_values = sorted({int(node.get("order", 0)) for node in frame_nodes})
        order_rank = {value: idx for idx, value in enumerate(order_values)}
        for node in frame_nodes:
            rank = order_rank[int(node.get("order", 0))]
            x = node_start_x + rank * column_step
            y = main_y if node["id"] in primary else branch_y
            box = (x, y, card_w, card_h)
            boxes[node["id"]] = box
            group, _ = card_elements(
                node, box, theme=theme, compact=True, focus_mode=False,
                decision_as_card=False, show_confidence=True,
            )
            shapes[node["id"]] = shape_from_group(group)
            cards.extend(group)
        cursor_y += panel_h + 42.0

    node_frame = {node["id"]: node.get("frame", "default") for node in diagram.get("nodes", [])}
    downward_slots: dict[tuple[str, str], int] = defaultdict(int)
    backward_slots: dict[str, int] = defaultdict(int)
    upper_slots: dict[str, int] = defaultdict(int)

    for edge in sorted(diagram.get("edges", []), key=lambda item: int(item.get("sequence", 0))):
        src, dst = edge.get("from"), edge.get("to")
        if src not in boxes or dst not in boxes:
            continue
        frame_id = node_frame.get(src, "default")
        primary = primary_by_frame.get(frame_id, set())
        source_main = src in primary
        target_main = dst in primary
        sb, tb = boxes[src], boxes[dst]
        scx, scy = center(sb)
        tcx, tcy = center(tb)

        if source_main and target_main and tcx > scx:
            sx, sy = anchor(sb, "right")
            tx, ty = anchor(tb, "left")
            points = [(sx + 5, sy), (tx - 5, ty)]
            label_pos = ((sx + tx) / 2, sy - 18)
        elif source_main and not target_main:
            slot_key = (frame_id, src)
            slot = downward_slots[slot_key]
            downward_slots[slot_key] += 1
            sx, sy = anchor(sb, "bottom")
            tx, ty = anchor(tb, "top")
            route_y = sy + 24.0 + slot * 20.0
            points = [(sx, sy + 5), (sx, route_y), (tx, route_y), (tx, ty - 5)]
            label_pos = ((sx + tx) / 2, route_y - 12)
        elif not source_main and target_main:
            slot = backward_slots[frame_id]
            backward_slots[frame_id] += 1
            sx, sy = anchor(sb, "bottom")
            tx, ty = anchor(tb, "bottom")
            route_y = max(sy, ty) + 36.0 + slot * 24.0
            points = [(sx, sy + 5), (sx, route_y), (tx, route_y), (tx, ty + 5)]
            label_pos = ((sx + tx) / 2, route_y - 12)
        elif not source_main and not target_main and tcx > scx:
            sx, sy = anchor(sb, "right")
            tx, ty = anchor(tb, "left")
            points = [(sx + 5, sy), (tx - 5, ty)]
            label_pos = ((sx + tx) / 2, sy - 18)
        else:
            slot = upper_slots[frame_id]
            upper_slots[frame_id] += 1
            sx, sy = anchor(sb, "top")
            tx, ty = anchor(tb, "top")
            route_y = min(sy, ty) - 38.0 - slot * 24.0
            points = [(sx, sy - 5), (sx, route_y), (tx, route_y), (tx, ty - 5)]
            label_pos = ((sx + tx) / 2, route_y - 12)

        parts = arrow_elements(
            edge, shapes[src], shapes[dst], points,
            theme=theme, show_label=True, label_position=label_pos,
        )
        line, lab = split_edge_parts(parts)
        edges.extend(line)
        labels.extend(lab)

    return scene_root(diagram, [*bg, *edges, *cards, *labels], theme=theme)

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

    # Compute content width from the widest frame before drawing the header.  Atlas
    # transition labels need real whitespace; the old fixed 270px column step left only
    # ~32px between 238px cards, so every non-trivial guard was painted over the nodes.
    dtype = diagram.get("type")
    column_step = 430.0 if dtype == "state-machine" else 256.0
    widest = 0
    for frame_id in ordered_frames:
        orders = sorted({int(n.get("order", 0)) for n in nodes_by_frame.get(frame_id, [])})
        widest = max(widest, len(orders))
    content_w = max(1740.0, 330.0 + widest * column_step)
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
                w, h = (220.0, 146.0) if is_decision else (220.0, 126.0)
                x = node_start_x + rank * column_step
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


def domain_icon(node: dict[str, Any]) -> str:
    text = " ".join([
        str(node.get("label") or ""),
        str(node.get("summary") or ""),
        " ".join(str(x) for x in node.get("source_refs", [])),
    ]).lower()
    if any(key in text for key in ("api", "접근", "route", "gateway")):
        return "api"
    if any(key in text for key in ("postgres", "database", "storage", "persistence", "저장")):
        return "storage"
    if any(key in text for key in ("qa", "quality", "검증", "evidence", "증거")):
        return "test"
    if any(key in text for key in ("recovery", "reconcile", "복구", "정합")):
        return "compensation"
    if any(key in text for key in ("heartbeat", "queue", "wakeup")):
        return "event"
    if any(key in text for key in ("workflow", "orchestration", "워크플로")):
        return "flow"
    if any(key in text for key in ("adapter", "external", "외부")):
        return "external"
    if any(key in text for key in ("issue", "작업")):
        return "note"
    if any(key in text for key in ("mission", "미션")):
        return "domain"
    return "worker" if node.get("kind") == "external" else "domain"


def is_foundation_domain(node: dict[str, Any]) -> bool:
    text = " ".join([
        str(node.get("label") or ""),
        str(node.get("summary") or ""),
        " ".join(str(x) for x in node.get("source_refs", [])),
    ]).lower()
    return any(key in text for key in ("postgres", "database", "storage", "persistence", "상태 저장"))


def domain_backbone(diagram: dict[str, Any]) -> list[str]:
    """Build a readable, model-driven main contract chain.

    The node order supplied by the visual model breaks cycles deterministically.  Direct
    predecessors of the reader's start node are prepended so API/input boundaries remain
    visible without turning the layout into a generic three-column wallpaper.
    """
    nodes = node_map(diagram)
    if not nodes:
        return []
    order = {nid: int(node.get("order", idx)) for idx, (nid, node) in enumerate(nodes.items())}
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for edge in sorted(diagram.get("edges", []), key=lambda e: int(e.get("sequence", 0))):
        src, dst = edge.get("from"), edge.get("to")
        if src not in nodes or dst not in nodes or src == dst:
            continue
        outgoing[src].append(dst)
        incoming[dst].append(src)

    start = diagram.get("reader_contract", {}).get("start_here_node_id")
    if start not in nodes or is_foundation_domain(nodes[start]):
        candidates = [nid for nid in nodes if not incoming[nid] and not is_foundation_domain(nodes[nid])]
        start = min(candidates or list(nodes), key=lambda nid: order[nid])

    memo: dict[str, list[str]] = {}
    visiting: set[str] = set()

    def best_from(nid: str) -> list[str]:
        if nid in memo:
            return memo[nid]
        if nid in visiting:
            return [nid]
        visiting.add(nid)
        candidates = [dst for dst in outgoing.get(nid, []) if order.get(dst, 0) > order.get(nid, 0) and not is_foundation_domain(nodes[dst])]
        paths = [[nid] + best_from(dst) for dst in candidates]
        visiting.remove(nid)
        best = max(paths, key=lambda p: (len(p), -sum(order[x] for x in p))) if paths else [nid]
        memo[nid] = best
        return best

    chain = best_from(start)
    predecessors = [src for src in incoming.get(start, []) if not is_foundation_domain(nodes[src]) and src not in chain]
    predecessors.sort(key=lambda nid: order[nid])
    chain = predecessors[-2:] + chain
    if len(chain) < 3:
        ordered = [nid for nid in sorted(nodes, key=lambda nid: order[nid]) if not is_foundation_domain(nodes[nid])]
        chain = ordered[: min(6, len(ordered))]
    return list(dict.fromkeys(chain))


def render_domain_overview(diagram: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    nodes = node_map(diagram)
    backbone = domain_backbone(diagram)
    foundation = [nid for nid, node in nodes.items() if is_foundation_domain(node)]
    support = [nid for nid in nodes if nid not in backbone and nid not in foundation]

    card_w, card_h, gap = 220.0, 158.0, 110.0
    margin = 78.0
    main_count = max(1, len(backbone))
    width = max(1900.0, margin * 2 + main_count * card_w + max(0, main_count - 1) * gap)
    support_cols = min(4, max(1, len(support)))
    support_rows = (len(support) + support_cols - 1) // support_cols if support else 0
    foundation_rows = 1 if foundation else 0
    panel_h = 350.0 + support_rows * 205.0 + foundation_rows * 205.0

    bg: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    header, content_y = header_elements(diagram, theme=theme, width=width, profile_label="DEEP ATLAS · 도메인 경계")
    bg.extend(header)
    frame = sorted(diagram.get("frames", []), key=lambda f: int(f.get("order", 0)))
    panel_title = frame[0].get("label") if frame else "업무 소유권과 계약"
    panel_subtitle = diagram.get("purpose") or (frame[0].get("purpose") if frame else "")
    bg.extend(panel_elements(
        "domain-boundary", 48, content_y, width - 96, panel_h,
        panel_title, panel_subtitle,
        theme=theme, accent=theme["primary"], role="domain-boundary",
    ))

    main_y = content_y + 136
    boxes: dict[str, tuple[float, float, float, float]] = {}
    shapes: dict[str, dict[str, Any]] = {}
    if backbone:
        total = len(backbone) * card_w + max(0, len(backbone) - 1) * gap
        main_x = (width - total) / 2
        for idx, nid in enumerate(backbone):
            boxes[nid] = (main_x + idx * (card_w + gap), main_y, card_w, card_h)

    support_y = main_y + card_h + 120
    if support:
        support_gap = 54.0
        support_w = 310.0
        for idx, nid in enumerate(support):
            row, col = divmod(idx, support_cols)
            row_items = min(support_cols, len(support) - row * support_cols)
            row_total = row_items * support_w + max(0, row_items - 1) * support_gap
            row_x = (width - row_total) / 2
            boxes[nid] = (row_x + col * (support_w + support_gap), support_y + row * 205.0, support_w, 158.0)

    foundation_y = support_y + support_rows * 205.0
    if foundation:
        bg.append(text_element(
            "domain-foundation-label:" + diagram["id"], margin, foundation_y - 34,
            "공통 상태·저장 기반", font_size=15, width=380, height=28, color=theme["muted"],
            align="left", valign="middle", font_family=theme["font_family"],
            custom_data={"imCodeMap": {"role": "foundation-label"}},
        ))
        foundation_gap = 54.0
        foundation_w = 330.0
        total = len(foundation) * foundation_w + max(0, len(foundation) - 1) * foundation_gap
        fx = (width - total) / 2
        for idx, nid in enumerate(foundation):
            boxes[nid] = (fx + idx * (foundation_w + foundation_gap), foundation_y, foundation_w, 158.0)

    for nid, node in nodes.items():
        box = boxes.get(nid)
        if not box:
            continue
        group, _ = card_elements(
            node, box, theme=theme, compact=False,
            icon_override=domain_icon(node), decision_as_card=True,
        )
        shapes[nid] = shape_from_group(group)
        cards.extend(group)

    backbone_index = {nid: idx for idx, nid in enumerate(backbone)}
    back_edge_index = 0
    for edge in sorted(diagram.get("edges", []), key=lambda e: int(e.get("sequence", 0))):
        src, dst = edge.get("from"), edge.get("to")
        if src not in boxes or dst not in boxes:
            continue
        sb, tb = boxes[src], boxes[dst]
        scx, scy = center(sb)
        tcx, tcy = center(tb)
        label_pos: tuple[float, float]
        if src in backbone_index and dst in backbone_index and backbone_index[dst] > backbone_index[src]:
            sx, sy = anchor(sb, "right"); tx, ty = anchor(tb, "left")
            points = [(sx + 5, sy), (tx - 5, ty)]
            label_pos = ((sx + tx) / 2, sy - 22)
        elif src in backbone_index and dst in backbone_index:
            sx, sy = anchor(sb, "top"); tx, ty = anchor(tb, "top")
            route_y = main_y - 38 - back_edge_index * 34
            back_edge_index += 1
            points = [(sx, sy - 5), (sx, route_y), (tx, route_y), (tx, ty - 5)]
            label_pos = ((sx + tx) / 2, route_y - 12)
        elif tcy > scy + 40:
            sx, sy = anchor(sb, "bottom"); tx, ty = anchor(tb, "top")
            mid_y = (sy + ty) / 2
            points = [(sx, sy + 5), (sx, mid_y), (tx, mid_y), (tx, ty - 5)]
            label_pos = ((sx + tx) / 2, mid_y - 12)
        elif tcy < scy - 40:
            sx, sy = anchor(sb, "top"); tx, ty = anchor(tb, "bottom")
            mid_y = (sy + ty) / 2
            points = [(sx, sy - 5), (sx, mid_y), (tx, mid_y), (tx, ty + 5)]
            label_pos = ((sx + tx) / 2, mid_y - 12)
        else:
            s_side = "right" if tcx >= scx else "left"
            t_side = "left" if tcx >= scx else "right"
            sx, sy = anchor(sb, s_side); tx, ty = anchor(tb, t_side)
            mid_x = (sx + tx) / 2
            points = [(sx, sy), (mid_x, sy), (mid_x, ty), (tx, ty)]
            label_pos = (mid_x, (sy + ty) / 2 - 12)
        parts = arrow_elements(
            edge, shapes[src], shapes[dst], points,
            theme=theme, show_label=True, label_position=label_pos,
        )
        line, lab = split_edge_parts(parts)
        edges.extend(line); labels.extend(lab)
    return scene_root(diagram, [*bg, *edges, *cards, *labels], theme=theme)


def render_diagram(diagram: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    dtype = diagram.get("type")
    if dtype == "human-overview":
        return render_human_overview(diagram, theme)
    if dtype == "focus-flow":
        return render_focus_flow(diagram, theme)
    if diagram.get("id") == "domain-commerce-overview" or dtype == "domain-overview":
        return render_domain_overview(diagram, theme)
    if dtype == "state-machine":
        return render_state_machine(diagram, theme)
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
