#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from overview_map_core import dump_json, load_json, validate_overview_map


def main() -> int:
    p = argparse.ArgumentParser(description="Validate a bounded overview map")
    p.add_argument("input")
    p.add_argument("--report")
    p.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = p.parse_args()
    report = validate_overview_map(load_json(args.input))
    if args.report:
        dump_json(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] and (not args.strict or not report["warnings"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
