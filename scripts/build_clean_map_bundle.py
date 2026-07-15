#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from overview_map_core import build_overview_map, dump_json, load_json, validate_overview_map
from clean_map_renderer import render_bundle


def main()->int:
    p=argparse.ArgumentParser(description="Build the v5.3 bounded overview map bundle")
    p.add_argument("--input",required=True); p.add_argument("--output-dir",required=True)
    p.add_argument("--project-name",required=True); p.add_argument("--project-slug")
    p.add_argument("--question",required=True); p.add_argument("--profile",default="orientation",choices=["orientation","focus","domain","change","debug"])
    p.add_argument("--stream-id"); p.add_argument("--source-ref"); p.add_argument("--max-nodes",type=int,default=20); p.add_argument("--max-edges",type=int,default=36)
    p.add_argument("--max-groups",type=int,default=4); p.add_argument("--max-embeds",type=int,default=4)
    a=p.parse_args(); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True); (out/"previews").mkdir(exist_ok=True)
    source=load_json(a.input)
    data=build_overview_map(source,project_name=a.project_name,project_slug=a.project_slug,question=a.question,profile=a.profile,stream_id=a.stream_id,source_ref=a.source_ref,max_nodes=a.max_nodes,max_edges=a.max_edges,max_groups=a.max_groups,max_embeds=a.max_embeds)
    report=validate_overview_map(data)
    if not report["ok"]: raise SystemExit("overview validation failed: "+"; ".join(report["errors"]))
    overview=out/"overview-map.json"; dump_json(overview,data)
    render=render_bundle(data,out/"overview-map.excalidraw",out/"previews/overview-map.svg",out/"previews/overview-map.png",out/"overview-map.layout.json")
    manifest={"version":"5.3.0","profile":a.profile,"question":a.question,"source":str(Path(a.input).resolve()),"overview":str(overview),"render":render,"validation":report}
    dump_json(out/"overview-map.manifest.json",manifest)
    print(json.dumps(manifest,ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
