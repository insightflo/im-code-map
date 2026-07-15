#!/usr/bin/env python3
"""Validate multilingual font coverage for generated SVG/PNG previews."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from clean_map_renderer import collect_render_text
from font_support import SVG_FONT_STACK, resolve_text_font
from overview_map_core import load_json


def validate(data_path: Path, svg_path: Path | None, png_path: Path | None) -> dict[str, object]:
    data = load_json(data_path)
    text = collect_render_text(data)
    errors: list[str] = []
    warnings: list[str] = []

    try:
        font = resolve_text_font(text)
        font_report = font.public_report()
    except Exception as exc:
        errors.append(str(exc))
        font_report = {
            "fontStack": SVG_FONT_STACK,
            "coverageVerified": False,
            "requiredCodepoints": 0,
        }

    if svg_path:
        if not svg_path.is_file():
            errors.append(f"SVG not found: {svg_path}")
        else:
            svg = svg_path.read_text(encoding="utf-8")
            if "Noto Sans CJK KR" not in svg or "NanumGothic" not in svg:
                errors.append("SVG is missing the multilingual Korean font fallback stack")
            if 'font-family="Arial, sans-serif"' in svg:
                errors.append("SVG still uses the Latin-only Arial-first font declaration")
            if any(char in text for char in "한글가나다") and "□" in svg:
                warnings.append("SVG text contains a literal white-square character")

    if png_path:
        if not png_path.is_file():
            errors.append(f"PNG not found: {png_path}")
        elif png_path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            errors.append(f"Invalid PNG signature: {png_path}")
        else:
            try:
                from PIL import Image

                with Image.open(png_path) as image:
                    if image.width < 100 or image.height < 100:
                        errors.append(f"PNG is unexpectedly small: {image.width}x{image.height}")
            except Exception as exc:
                errors.append(f"PNG could not be decoded: {exc}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "font": font_report,
        "inputs": {
            "data": str(data_path),
            "svg": str(svg_path) if svg_path else None,
            "png": str(png_path) if png_path else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path, help="overview-map.json")
    parser.add_argument("--svg", type=Path)
    parser.add_argument("--png", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()

    result = validate(args.data, args.svg, args.png)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] and (not args.strict_warnings or not result["warnings"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
