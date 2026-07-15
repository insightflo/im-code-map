#!/usr/bin/env python3
from __future__ import annotations
import argparse
from overview_map_core import build_overview_map, dump_json, load_json, validate_overview_map


def main() -> int:
    p = argparse.ArgumentParser(description="Project a rich im-code-map model into a bounded overview map")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--project-name", required=True)
    p.add_argument("--project-slug")
    p.add_argument("--question", required=True)
    p.add_argument("--profile", default="orientation", choices=["orientation", "focus", "domain", "change", "debug"])
    p.add_argument("--stream-id")
    p.add_argument("--source-ref")
    p.add_argument("--max-nodes", type=int, default=20)
    p.add_argument("--max-edges", type=int, default=36)
    p.add_argument("--max-groups", type=int, default=4)
    p.add_argument("--max-embeds", type=int, default=4)
    args = p.parse_args()
    result = build_overview_map(
        load_json(args.input), project_name=args.project_name, project_slug=args.project_slug,
        question=args.question, profile=args.profile, stream_id=args.stream_id,
        source_ref=args.source_ref, max_nodes=args.max_nodes, max_edges=args.max_edges,
        max_groups=args.max_groups, max_embeds=args.max_embeds,
    )
    report = validate_overview_map(result)
    if not report["ok"]:
        raise SystemExit("overview validation failed: " + "; ".join(report["errors"]))
    dump_json(args.output, result)
    print(f"overview map: {report['counts']} warnings={len(report['warnings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
