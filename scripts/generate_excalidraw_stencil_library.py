#!/usr/bin/env python3
"""Generate the package-owned Excalidraw stencil library and a visual catalog.

The library contains only native Excalidraw primitives authored by this package.
It deliberately avoids vendor logos, emoji, and copied third-party library items.
"""
from __future__ import annotations

import argparse
import copy
import time
from pathlib import Path
from typing import Any

from excalidraw_design_system import (
    card_elements,
    chip_elements,
    load_design,
    rectangle,
    scene_root,
    shadow_element,
    text_element,
)
from im_code_map_common import scene_bounds, stable_id, write_json


STENCILS: list[dict[str, str]] = [
    {"id": "actor", "name": "Actor / 사용자", "kind": "actor", "label": "사용자", "summary": "업무 흐름을 시작하는 사람 또는 역할"},
    {"id": "service", "name": "Service / 서비스", "kind": "process", "icon": "service", "label": "주문 서비스", "summary": "업무 규칙을 실행하고 다른 컴포넌트를 조정"},
    {"id": "decision-card", "name": "Decision card / 판단", "kind": "decision", "label": "주문 가능한가?", "summary": "정책과 현재 상태를 기준으로 흐름을 분기"},
    {"id": "decision-diamond", "name": "Decision diamond / 상세 판단", "kind": "decision", "label": "승인됐는가?", "summary": "Atlas의 명시적 조건 분기"},
    {"id": "state", "name": "State transition / 상태 전이", "kind": "state-change", "label": "주문 상태 변경", "summary": "업무 엔티티의 전후 상태", "before": "PENDING", "after": "PAID"},
    {"id": "event", "name": "Event / 비동기 이벤트", "kind": "event", "label": "order.placed", "summary": "커밋 이후 후속 처리를 깨우는 이벤트"},
    {"id": "storage", "name": "Database / 저장소", "kind": "storage", "label": "주문 저장소", "summary": "상태와 이력을 영속적으로 저장"},
    {"id": "queue", "name": "Queue / 메시지 큐", "kind": "process", "icon": "queue", "label": "이벤트 큐", "summary": "생산자와 소비자의 비동기 경계"},
    {"id": "external", "name": "External system / 외부 시스템", "kind": "external", "label": "결제 게이트웨이", "summary": "네트워크·timeout·재시도 경계"},
    {"id": "risk", "name": "Risk / 미확인 경계", "kind": "risk", "label": "확인이 필요한 것", "summary": "현재 설명 또는 안전한 변경을 막는 모름"},
    {"id": "compensation", "name": "Compensation / 보상", "kind": "compensation", "label": "재고 해제", "summary": "부분 성공을 되돌려 일관성을 복원"},
    {"id": "end", "name": "Outcome / 종료 결과", "kind": "end", "label": "주문 완료", "summary": "사용자에게 관찰되는 최종 결과"},
    {"id": "domain", "name": "Domain / 도메인", "kind": "domain", "label": "Ordering", "summary": "명확한 책임과 계약을 가진 업무 경계"},
    {"id": "atlas", "name": "Deep Atlas link / 상세 지도", "kind": "note", "icon": "atlas", "label": "Deep Atlas 열기", "summary": "상태·오류·보상·코드 근거로 확장"},
]


def normalize_elements(elements: list[dict[str, Any]], namespace: str) -> list[dict[str, Any]]:
    active = [copy.deepcopy(e) for e in elements if not e.get("isDeleted")]
    bx, by, _, _ = scene_bounds(active)
    id_map = {e["id"]: stable_id(e.get("type", "el")[:3], namespace + ":" + e["id"]) for e in active}
    group_map: dict[str, str] = {}
    for element in active:
        for gid in element.get("groupIds", []) or []:
            group_map.setdefault(gid, stable_id("grp", namespace + ":" + gid))
    for e in active:
        old_id = e["id"]
        e["id"] = id_map[old_id]
        e["x"] = round(float(e.get("x", 0)) - bx, 2)
        e["y"] = round(float(e.get("y", 0)) - by, 2)
        e["groupIds"] = [group_map.get(g, g) for g in (e.get("groupIds") or [])]
        if e.get("boundElements"):
            e["boundElements"] = [{**b, "id": id_map.get(b.get("id"), b.get("id"))} for b in e["boundElements"]]
        for binding_key in ("startBinding", "endBinding"):
            if e.get(binding_key):
                e[binding_key]["elementId"] = id_map.get(e[binding_key].get("elementId"), e[binding_key].get("elementId"))
    return active


def build_card(stencil: dict[str, str], x: float, y: float, *, theme: dict[str, Any], preview: bool) -> list[dict[str, Any]]:
    node: dict[str, Any] = {
        "id": "stencil-" + stencil["id"],
        "label": stencil["label"],
        "kind": stencil["kind"],
        "summary": stencil["summary"],
        "source_refs": ["im-code-map-v5.1-design-system"],
        "confidence": "VERIFIED",
        "details_link": None,
    }
    if stencil.get("before") or stencil.get("after"):
        node["state_before"] = stencil.get("before")
        node["state_after"] = stencil.get("after")
    decision_as_card = stencil["id"] != "decision-diamond"
    width, height = (340.0, 170.0) if decision_as_card else (300.0, 190.0)
    group, _ = card_elements(
        node, (x, y, width, height), theme=theme, compact=False,
        icon_override=stencil.get("icon") or stencil["kind"], decision_as_card=decision_as_card,
    )
    if preview:
        return group
    return normalize_elements(group, "library:" + stencil["id"])


def build_catalog(theme: dict[str, Any]) -> dict[str, Any]:
    fake = {
        "id": "im-code-map-stencil-library-preview",
        "type": "stencil-library",
        "title": "im-code-map Architecture Stencil Library",
        "purpose": "Focus와 Deep Atlas에서 사용하는 편집 가능한 기본 컴포넌트입니다.",
        "nodes": [],
        "edges": [],
    }
    elements: list[dict[str, Any]] = []
    elements.extend([
        text_element(
            "library-eyebrow", 54, 34, "IM-CODE-MAP v5.1 · NATIVE EXCALIDRAW COMPONENTS",
            font_size=13, width=600, height=30, color=theme["primary"], align="left",
            valign="middle", font_family=theme["font_family"],
            custom_data={"imCodeMap": {"role": "profile-chip-text"}},
        ),
        text_element(
            "library-title", 54, 78, fake["title"], font_size=40, width=1200,
            height=58, color=theme["ink"], align="left", valign="middle",
            font_family=theme["font_family"], custom_data={"imCodeMap": {"role": "diagram-title"}},
        ),
        text_element(
            "library-subtitle", 54, 138,
            "외부 로고나 이모지 없이, 같은 아이콘·색·카드 규칙으로 흐름을 조립합니다.",
            font_size=16, width=1200, height=42, color=theme["muted"], align="left",
            valign="middle", font_family=theme["font_family"],
            custom_data={"imCodeMap": {"role": "diagram-purpose"}},
        ),
    ])
    cols = 3
    card_w, cell_w, cell_h = 340.0, 480.0, 262.0
    start_x, start_y = 54.0, 230.0
    rows = (len(STENCILS) + cols - 1) // cols
    panel_w = cols * cell_w + 34
    panel_h = rows * cell_h + 54
    elements.extend([
        shadow_element("library-panel-shadow", start_x - 20, start_y - 22, panel_w, panel_h, theme=theme),
        rectangle(
            "library-panel", start_x - 20, start_y - 22, panel_w, panel_h,
            theme=theme, stroke=theme["border"], background=theme["surface"],
            stroke_width=1.3, role="library-panel",
        ),
    ])
    for idx, stencil in enumerate(STENCILS):
        col, row = idx % cols, idx // cols
        x = start_x + col * cell_w
        y = start_y + row * cell_h
        chip, _ = chip_elements(
            f"library-name:{stencil['id']}", x, y, stencil["name"], theme=theme,
            color=theme["muted"], background=theme["surface_alt"], font_size=11,
            min_width=190, role="stencil-name",
        )
        elements.extend(chip)
        elements.extend(build_card(stencil, x, y + 44, theme=theme, preview=True))
    return scene_root(fake, elements, theme=theme, source="im-code-map-v5.1-stencil-library")


def build_library(theme: dict[str, Any]) -> dict[str, Any]:
    created = 1  # deterministic; Excalidraw accepts an epoch-like integer here.
    items: list[dict[str, Any]] = []
    for stencil in STENCILS:
        elements = build_card(stencil, 0, 0, theme=theme, preview=False)
        items.append({
            "id": stable_id("lib", "im-code-map:" + stencil["id"]),
            "status": "published",
            "created": created,
            "name": stencil["name"],
            "elements": elements,
        })
    return {
        "type": "excalidrawlib",
        "version": 2,
        "source": "im-code-map-v5.1",
        "libraryItems": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", default=Path("libraries/im-code-map-architecture.excalidrawlib"))
    parser.add_argument("--preview", type=Path, default=Path("libraries/im-code-map-architecture-preview.excalidraw"))
    parser.add_argument("--theme", choices=["clean", "whiteboard"], default="clean")
    args = parser.parse_args()
    theme = load_design(args.theme)
    write_json(args.output, build_library(theme))
    write_json(args.preview, build_catalog(theme))
    print(f"WROTE {args.output}")
    print(f"WROTE {args.preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
