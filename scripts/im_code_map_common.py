#!/usr/bin/env python3
"""Shared deterministic helpers for im-code-map v5 generators and validators."""
from __future__ import annotations

import hashlib
import json
import math
import re
import textwrap
from pathlib import Path
from typing import Any, Iterable

VALID_CONFIDENCE = {"VERIFIED", "PARTIAL", "DOC_ONLY", "UNVERIFIED", "CONFLICT"}

SEMANTIC_COLORS = {
    "actor": ("#1c7ed6", "#e7f5ff"),
    "start": ("#2b8a3e", "#ebfbee"),
    "process": ("#495057", "#f8f9fa"),
    "decision": ("#e67700", "#fff4e6"),
    "state-change": ("#7048e8", "#f3f0ff"),
    "event": ("#0b7285", "#e3fafc"),
    "wait": ("#5f3dc4", "#f3f0ff"),
    "data": ("#1864ab", "#e7f5ff"),
    "storage": ("#1864ab", "#e7f5ff"),
    "external": ("#862e9c", "#f8f0fc"),
    "error": ("#c92a2a", "#fff5f5"),
    "compensation": ("#a61e4d", "#fff0f6"),
    "end": ("#2b8a3e", "#ebfbee"),
    "domain": ("#364fc7", "#edf2ff"),
    "codebase": ("#343a40", "#f1f3f5"),
    "note": ("#5c940d", "#f4fce3"),
    "risk": ("#c92a2a", "#fff5f5"),
    "test": ("#087f5b", "#e6fcf5"),
}

EDGE_COLORS = {
    "happy-path": "#2b8a3e",
    "conditional": "#e67700",
    "async-event": "#0b7285",
    "retry": "#5f3dc4",
    "error": "#c92a2a",
    "timeout": "#c92a2a",
    "compensation": "#a61e4d",
    "cancel": "#c92a2a",
    "data": "#1864ab",
    "reference": "#868e96",
    "dependency": "#495057",
    "ownership": "#364fc7",
}


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(prefix: str, key: str) -> str:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def stable_int(key: str, maximum: int = 2_000_000_000) -> int:
    value = int(hashlib.sha1(key.encode("utf-8")).hexdigest()[:12], 16)
    return 1 + (value % maximum)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9가-힣._-]+", "-", value)
    return value.strip("-") or "item"


def clamp_text(value: str, max_words: int = 28, max_chars: int = 220) -> str:
    normalized = " ".join(str(value or "").split())
    words = normalized.split()
    if len(words) > max_words:
        normalized = " ".join(words[:max_words]) + "…"
    if len(normalized) > max_chars:
        normalized = normalized[: max_chars - 1].rstrip() + "…"
    return normalized


def wrap_text(value: str, width: int = 28, max_lines: int = 6) -> str:
    lines: list[str] = []
    for paragraph in str(value or "").splitlines() or [""]:
        wrapped = textwrap.wrap(paragraph, width=max(8, width), break_long_words=False, break_on_hyphens=False) or [""]
        lines.extend(wrapped)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip("…") + "…"
    return "\n".join(lines)


def estimate_text_box(text: str, font_size: int, max_width: int) -> tuple[int, int]:
    char_width = max(6.0, font_size * 0.56)
    line_height = font_size * 1.25
    lines = text.splitlines() or [""]
    width = min(max_width, max(40, int(max((len(line) for line in lines), default=1) * char_width + 8)))
    height = max(int(line_height + 4), int(len(lines) * line_height + 8))
    return width, height


def evidence_text(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        source = item.get("source", "source")
        locator = item.get("locator", "")
        return f"{source}#{locator}" if locator else str(source)
    return str(item)


def ensure_unique_ids(items: Iterable[dict[str, Any]], label: str) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for item in items:
        item_id = item.get("id")
        if item_id in seen:
            duplicates.append(str(item_id))
        seen.add(item_id)
    return duplicates


def boxes_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float], margin: float = 4) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (
        ax + aw + margin <= bx
        or bx + bw + margin <= ax
        or ay + ah + margin <= by
        or by + bh + margin <= ay
    )


def center(box: tuple[float, float, float, float]) -> tuple[float, float]:
    x, y, w, h = box
    return x + w / 2, y + h / 2


def anchor_points(source: tuple[float, float, float, float], target: tuple[float, float, float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
    sx, sy, sw, sh = source
    tx, ty, tw, th = target
    scx, scy = center(source)
    tcx, tcy = center(target)
    dx, dy = tcx - scx, tcy - scy
    if abs(dx) >= abs(dy):
        start = (sx + sw if dx >= 0 else sx, scy)
        end = (tx if dx >= 0 else tx + tw, tcy)
    else:
        start = (scx, sy + sh if dy >= 0 else sy)
        end = (tcx, ty if dy >= 0 else ty + th)
    return start, end


def transform_point(point: list[float] | tuple[float, float], scale: float, dx: float, dy: float) -> list[float]:
    return [float(point[0]) * scale + dx, float(point[1]) * scale + dy]


def scene_bounds(elements: Iterable[dict[str, Any]], include_frames: bool = True) -> tuple[float, float, float, float]:
    boxes = []
    for e in elements:
        if e.get("isDeleted"):
            continue
        if not include_frames and e.get("type") == "frame":
            continue
        boxes.append((float(e.get("x", 0)), float(e.get("y", 0)), float(e.get("width", 0)), float(e.get("height", 0))))
    if not boxes:
        return (0, 0, 0, 0)
    min_x = min(x for x, _, _, _ in boxes)
    min_y = min(y for _, y, _, _ in boxes)
    max_x = max(x + w for x, _, w, _ in boxes)
    max_y = max(y + h for _, y, _, h in boxes)
    return min_x, min_y, max_x - min_x, max_y - min_y


def euclidean(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
