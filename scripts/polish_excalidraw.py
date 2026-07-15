#!/usr/bin/env python3
"""Normalize legacy im-code-map Excalidraw scenes to the v5.3 clean theme.

This is deliberately conservative: it changes styling and canvas background,
but it does not move elements, rewrite bindings, or reorder frame children.
"""
from __future__ import annotations
import argparse, json
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
SOFTEN = {
    "#ffe8e8": "#fef2f2", "#fff3d6": "#fff7e6", "#e8f1ff": "#eff6ff",
    "#eef7f1": "#ecfdf5", "#f3e8ff": "#f5f3ff", "#e0f2fe": "#f0f9ff",
}


def is_background_role(el: dict[str, Any]) -> bool:
    role = str((el.get("customData") or {}).get("role", "")).lower()
    return role in {"group", "lane", "frame-background", "section", "background"}


def polish_scene(scene: dict[str, Any]) -> dict[str, Any]:
    scene = dict(scene)
    app = dict(scene.get("appState") or {})
    app.update({"viewBackgroundColor": CANVAS_BG, "currentItemRoughness": 0, "currentItemStrokeWidth": 1})
    scene["appState"] = app
    result: list[dict[str, Any]] = []
    for original in scene.get("elements", []):
        if not isinstance(original, dict):
            continue
        el = dict(original)
        etype = el.get("type")
        el["roughness"] = 0
        el["fillStyle"] = "solid"
        if etype in {"arrow", "line"}:
            edge_kind = str((el.get("customData") or {}).get("edgeKind", "normal"))
            if edge_kind == "normal" or not el.get("customData"):
                el["strokeColor"] = EDGE
            el["strokeWidth"] = min(2, max(1, float(el.get("strokeWidth", 1.25))))
            if el.get("roundness") is None:
                el["roundness"] = {"type": 2}
        elif etype == "text":
            size = int(el.get("fontSize", 16) or 16)
            el["strokeColor"] = TEXT if size >= 14 else MUTED
            el["fontFamily"] = 1
        elif etype in {"rectangle", "diamond", "ellipse"}:
            area = abs(float(el.get("width", 0)) * float(el.get("height", 0)))
            current_fill = str(el.get("backgroundColor", "transparent")).lower()
            if current_fill in SOFTEN:
                el["backgroundColor"] = SOFTEN[current_fill]
            if etype == "rectangle":
                if is_background_role(el) or area >= 180000:
                    el["backgroundColor"] = GROUP_BG
                    el["strokeColor"] = GROUP_STROKE
                    el["strokeWidth"] = 1
                    el["opacity"] = min(88, int(el.get("opacity", 100)))
                elif area >= 10000:
                    el["backgroundColor"] = CARD_BG
                    el["strokeColor"] = CARD_STROKE
                    el["strokeWidth"] = min(1.25, max(0.8, float(el.get("strokeWidth", 1))))
                    el["opacity"] = 100
                if el.get("roundness") is None:
                    el["roundness"] = {"type": 3}
        result.append(el)
    scene["elements"] = result
    meta = dict(scene.get("imCodeMap") or {})
    meta.update({"theme": "clean-v2", "polishedBy": "im-code-map-v5.3.1"})
    scene["imCodeMap"] = meta
    return scene


def main() -> int:
    p = argparse.ArgumentParser(description="Apply the v5.3 clean style to an Excalidraw scene or directory")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    src, dst = Path(args.input), Path(args.output)
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        files = sorted(src.rglob("*.excalidraw"))
        for path in files:
            rel = path.relative_to(src)
            out = dst / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(polish_scene(json.loads(path.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(f"polished {len(files)} scenes")
        return 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(polish_scene(json.loads(src.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"polished {src} -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
