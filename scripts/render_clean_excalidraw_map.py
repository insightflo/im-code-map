#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from overview_map_core import load_json, validate_overview_map
from clean_map_renderer import render_bundle


def main() -> int:
    p = argparse.ArgumentParser(description="Render a bounded overview map with the clean v5.3 Excalidraw design")
    p.add_argument("--input", required=True)
    p.add_argument("--excalidraw", required=True)
    p.add_argument("--svg")
    p.add_argument("--png")
    p.add_argument("--layout-json")
    args = p.parse_args()
    data = load_json(args.input)
    report = validate_overview_map(data)
    if not report["ok"]:
        raise SystemExit("overview validation failed: " + "; ".join(report["errors"]))
    result = render_bundle(data, args.excalidraw, args.svg, args.png, args.layout_json)
    print(json.dumps({"render": result, "validation": report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
