#!/usr/bin/env python3
"""Migrate v4 shared/Atlas models into v5 scaffolding.

The migration preserves evidence and Atlas structure. It cannot invent a human
question, stop condition, relevant unknowns, or Focus narrative, so those outputs
are explicitly marked UNVERIFIED until the codebase is re-read for a real task.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from im_code_map_common import read_json, write_json

TRIGGERS=["authentication","authorization","payment","privacy","data-deletion","migration","concurrency","idempotency","retry-compensation","cross-repository","conflicting-evidence","dynamic-dispatch","broad-state-change","user-request"]

ATLAS_PREFIXES=(
    "actors/", "domains/", "entities/", "states/", "rules/", "codebases/",
    "flows/", "indexes/", "excalidraw/", "previews/",
    "excalidraw-automate/",
)

def atlas_path(value: Any) -> Any:
    """Move v4 detailed-output paths below architecture/atlas.

    Paths outside architecture/*, machine paths, and already-migrated paths are
    preserved. The Focus projection is generated later from a real question and
    must not be fabricated by migration.
    """
    if not isinstance(value, str) or not value.startswith("architecture/"):
        return value
    if value.startswith("architecture/atlas/"):
        return value
    rel=value[len("architecture/"):]
    if rel == "workspace-stream-map.canvas":
        return "architecture/atlas/workspace-stream-map.canvas"
    if rel in {"start-here.md", "visual-index.md", "index.md"}:
        return f"architecture/atlas/{rel}"
    if rel.startswith(ATLAS_PREFIXES):
        return f"architecture/atlas/{rel}"
    return value

def normalize_atlas_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: normalize_atlas_paths(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_atlas_paths(v) for v in value]
    return atlas_path(value)

def reader_contract(diagram:dict[str,Any])->dict[str,Any]:
    nodes=diagram.get("nodes",[]); ids=[n.get("id") for n in nodes if n.get("id")]
    start=next((n["id"] for n in nodes if n.get("kind")=="start"),ids[0] if ids else "missing")
    primary=[n["id"] for n in nodes if n.get("kind") not in {"error","compensation"}][:30] or ids[:1]
    return {"start_here_node_id":start,"primary_story_node_ids":primary,"answers":{"who_starts":"Migrated Atlas; re-verify actor.","what_they_want":diagram.get("purpose","Migrated behavior"),"key_decisions":"See migrated branches; re-verify conditions.","success_change":"See migrated terminal outcomes; re-verify state effects."},"does_not_answer":["A task-scoped Focus view has not been created."],"stop_reasons":[],"deeper_links":diagram.get("navigation",{}).get("related_notes",[]),"required_unknowns":["Focus question and current risk boundary are not yet established."]}

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("v4_map",type=Path); ap.add_argument("v4_visual",type=Path); ap.add_argument("output_dir",type=Path)
    a=ap.parse_args(); out=a.output_dir; out.mkdir(parents=True,exist_ok=True); now=datetime.now(timezone.utc).isoformat()
    m=normalize_atlas_paths(read_json(a.v4_map)); m["schema_version"]="5.0.0"; m["profile_support"]={"default_profile":"focus","supported_profiles":["focus","atlas"],"default_workflows":["orient","trace","explain","before-change","debug","expand"],"atlas_escalation_triggers":TRIGGERS}
    v=normalize_atlas_paths(read_json(a.v4_visual)); v["schema_version"]="5.0.0"; v["profile"]="atlas"; v["source_understanding_session"]=None; v["reader_policy"]={"intended_reader":"reviewer","primary_question":"Migrated v4 Atlas; establish a real v5 understanding question before using Focus.","first_view_target_seconds":180,"detail_policy":"full-detail","implementation_identifiers":"notes-only","max_primary_story_nodes":30,"failure_detail_mode":"full-branches","show_step_numbers":False}
    for d in v.get("diagrams",[]): d["profile"]="atlas"; d.setdefault("reader_contract",reader_contract(d))
    stream=(m.get("business_streams") or [{}])[0].get("id")
    session={"schema_version":"5.0.0","workspace_id":m.get("workspace_id","migrated"),"session_id":"migrated-v4-needs-question","created_at":now,"question":"Which concrete user or operational flow should be understood first?","intent":"orient","requested_depth":"default","audience":"newcomer","selected_stream_id":stream,"expected_outcome":"Choose one evidenced end-to-end flow and define a human stop condition.","stop_condition":"A real question, scope, and current relevant unknowns are recorded.","scope":{"in_scope":["Select one first flow"],"out_of_scope":["No Focus narrative is approved by migration alone"]},"risk_assessment":{"level":"medium","triggers":[],"requires_atlas":False,"reason":"Migration does not assess current change risk."},"routing_decision":{"selected_profile":"focus","automatic_escalation":False,"reason":"Create a task-scoped Focus after re-analysis."},"evidence":["Migrated from v4; no new source verification performed."]}
    coverage={"schema_version":"5.0.0","workspace_id":m.get("workspace_id","migrated"),"session_id":session["session_id"],"explored":[{"id":"migrated-atlas","label":"Existing v4 Atlas model","reason":"Preserved for compatibility.","impact":"relevant-later","next_check":None,"source_refs":[],"confidence":"UNVERIFIED"}],"unknown_relevant":[{"id":"unknown-focus-question","label":"Task-scoped Focus question and stop condition","reason":"v4 did not require an understanding session.","impact":"blocks-answer","next_check":"Ask what behavior or change the reader needs to understand.","source_refs":[],"confidence":"UNVERIFIED"}],"unknown_out_of_scope":[],"expansion_points":[],"boundaries":[],"completion":{"question_answered":False,"stop_condition_met":False,"safe_to_change":"no","atlas_recommended":True,"notes":["Migration preserves structure but does not certify current behavior."]}}
    write_json(out/"map-model.json",m); write_json(out/"atlas-visual-model.json",v); write_json(out/"understanding-session.json",session); write_json(out/"coverage.json",coverage)
    (out/"MIGRATION.md").write_text("# v4 → v5 migration\n\nAtlas evidence was preserved. Focus, current unknowns, and change safety require source re-analysis.\n",encoding="utf-8")
    print(f"WROTE v5 migration scaffold to {out}"); return 0
if __name__=='__main__': raise SystemExit(main())
