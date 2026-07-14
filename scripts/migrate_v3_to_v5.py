#!/usr/bin/env python3
"""Migrate legacy im-code-map output to an explicitly incomplete v5 shared-model skeleton.

The migration does not invent actors, guards, state machines, or business rules.
Unknowns are marked UNVERIFIED and listed in a remediation report.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from im_code_map_common import read_json, write_json

TYPE_MAP = {"business":"business","platform":"platform","cross-cutting":"cross-cutting","cross_cutting":"cross-cutting","supporting":"supporting","external":"external"}

def ev(source: str, locator: str, excerpt: str = "") -> list[dict[str,str]]:
    item={"source":source,"locator":locator,"tool":"legacy-migration"}
    if excerpt: item["excerpt"]=excerpt
    return [item]

def domain_type(value: Any) -> str:
    return TYPE_MAP.get(str(value or "").strip().lower(), "supporting")

def guess_domain(text: str, known: set[str], fallback: str) -> str:
    for candidate in re.findall(r"\(([a-z0-9-]+)\)", text.lower()):
        if candidate in known: return candidate
    for candidate in known:
        if candidate in text.lower(): return candidate
    return fallback

def migrate(old: dict[str,Any], source_path: Path) -> tuple[dict[str,Any], str]:
    old_domains=old.get("domains",[])
    domain_ids={d.get("id") for d in old_domains if d.get("id")}
    old_flows=old.get("cross_domain_flows") or old.get("flows") or []
    codebase_names=sorted({str(cb) for d in old_domains for cb in d.get("codebases",[])})
    stream_ids={f.get("id") or f"legacy-flow-{i+1}" for i,f in enumerate(old_flows)}
    participation={did:[] for did in domain_ids}
    streams=[]
    for i,f in enumerate(old_flows):
        sid=f.get("id") or f"legacy-flow-{i+1}"
        origin=f.get("from") if f.get("from") in domain_ids else (next(iter(domain_ids)) if domain_ids else "legacy-context")
        path=f.get("path") or f.get("steps") or []
        if isinstance(path,str): path=[path]
        steps=[]; transitions=[]; touched=[origin]
        steps.append({"id":f"{sid}.start","sequence":0,"name":"Unverified trigger","kind":"start","actor_id":"unknown-initiator","domain_id":origin,"action":"Legacy output did not record the actor, trigger, or entry point.","inputs":[],"outputs":[],"reads":[],"writes":[],"state_changes":[],"rule_refs":[],"implementation_refs":[],"details_note":f"architecture/atlas/flows/{sid}.md","evidence":ev(str(source_path),f"cross_domain_flows[{i}]","trigger absent"),"confidence":"UNVERIFIED"})
        prev=f"{sid}.start"
        for j,item in enumerate(path,1):
            text=str(item)
            did=guess_domain(text,domain_ids,origin)
            touched.append(did)
            step_id=f"{sid}.legacy-{j}"
            steps.append({"id":step_id,"sequence":j,"name":f"Legacy stage {j}","kind":"process","actor_id":"papercompany-system","domain_id":did,"action":text,"inputs":[],"outputs":[],"reads":[],"writes":[],"state_changes":[],"rule_refs":[],"implementation_refs":[],"details_note":f"architecture/atlas/flows/{sid}.md","evidence":ev(str(source_path),f"cross_domain_flows[{i}].path[{j-1}]",text),"confidence":"DOC_ONLY"})
            transitions.append({"id":f"{sid}.t{j}","from":prev,"to":step_id,"kind":"happy-path","label":"legacy order","condition":"sequence only; runtime condition not recorded","priority":j,"evidence":ev(str(source_path),f"cross_domain_flows[{i}].path[{j-1}]"),"confidence":"DOC_ONLY"})
            prev=step_id
        end_id=f"{sid}.end"
        steps.append({"id":end_id,"sequence":len(path)+1,"name":"Unverified terminal result","kind":"end","actor_id":"papercompany-system","domain_id":touched[-1],"action":"Legacy output did not record observable success/failure outcomes.","inputs":[],"outputs":[],"reads":[],"writes":[],"state_changes":[],"rule_refs":[],"implementation_refs":[],"details_note":f"architecture/atlas/flows/{sid}.md","evidence":ev(str(source_path),f"cross_domain_flows[{i}]","outcome absent"),"confidence":"UNVERIFIED"})
        transitions.append({"id":f"{sid}.t-end","from":prev,"to":end_id,"kind":"happy-path","label":"legacy end","condition":"terminal condition not recorded","priority":len(path)+1,"evidence":ev(str(source_path),f"cross_domain_flows[{i}]"),"confidence":"UNVERIFIED"})
        for did in set(touched): participation.setdefault(did,[]).append(sid)
        streams.append({"id":sid,"name":f.get("note") or sid,"purpose":f.get("note") or "Migrated legacy cross-domain path.","actor_ids":["unknown-initiator","papercompany-system"],"domain_ids":list(dict.fromkeys(touched)),"trigger":{"kind":"system","source":"UNVERIFIED","event":"UNVERIFIED legacy trigger","entry_point":"UNVERIFIED"},"preconditions":[],"start_step_id":f"{sid}.start","steps":steps,"transitions":transitions,"outcomes":[{"id":f"{sid}.unknown-outcome","type":"partial","terminal_step_id":end_id,"description":"Legacy output ends here","observable_result":"UNVERIFIED"}],"error_paths":[],"compensations":[],"state_changes":[],"evidence":ev(str(source_path),f"cross_domain_flows[{i}]"),"confidence":"UNVERIFIED","diagram_paths":[f"architecture/atlas/excalidraw/stream-{sid}.excalidraw"],"note_path":f"architecture/atlas/flows/{sid}.md"})
    domains=[]
    for i,d in enumerate(old_domains):
        impl={}
        flat=[]
        for layer,paths in (d.get("layers") or {}).items():
            for p in paths if isinstance(paths,list) else [paths]: flat.append(f"{layer}: {p}")
        for cb in d.get("codebases",[]): impl[str(cb)]=flat
        domains.append({"id":d["id"],"name":d.get("name",d["id"]),"type":domain_type(d.get("type")),"purpose":d.get("purpose","Legacy purpose not recorded."),"responsibilities":[],"implementations_by_codebase":impl,"owned_entities":[],"owned_state_machines":[],"participating_streams":participation.get(d["id"],[]),"overview_diagram":f"architecture/atlas/excalidraw/domain-{d['id']}-overview.excalidraw","note_path":f"architecture/atlas/domains/domain-{d['id']}.md","evidence":ev(str(source_path),f"domains[{i}]",d.get("purpose","")),"confidence":d.get("confidence","DOC_ONLY") if d.get("confidence") in {"VERIFIED","PARTIAL","DOC_ONLY","UNVERIFIED","CONFLICT"} else "DOC_ONLY"})
    model={"schema_version":"5.0.0","workspace_id":old.get("workspace_id","legacy-workspace"),"generated_at":old.get("generated_at","2026-07-10T00:00:00+09:00"),"source_tools":[{"name":"legacy-im-code-map","status":"AVAILABLE","version":str(old.get("schema_version","unknown")),"scope":str(source_path),"evidence":ev(str(source_path),"<root>")}],"confidence":"UNVERIFIED","tool_status":{"normal_mode":False,"evidence_mode":"degraded","codegraph":"PARTIAL","snapshot":"NOT_APPLICABLE","documentation":"AGENT_NATIVE","notes":["Migrated from a legacy summary model; re-analysis is required."]},"documentation_provider":"agent-native-docs","profile_support":{"default_profile":"focus","supported_profiles":["focus","atlas"],"default_workflows":["orient","trace","explain","before-change","debug","expand"],"atlas_escalation_triggers":["authentication","authorization","payment","privacy","data-deletion","migration","concurrency","idempotency","retry-compensation","cross-repository","conflicting-evidence","dynamic-dispatch","broad-state-change","user-request"]},"codebases":[{"id":cb,"name":cb,"root_path":"UNVERIFIED","kind":"unknown","languages":[],"entry_points":[],"evidence":ev(str(source_path),f"codebase:{cb}"),"confidence":"UNVERIFIED"} for cb in codebase_names],"actors":[{"id":"unknown-initiator","name":"Unknown initiator","type":"human","roles":[],"entry_points":[],"permissions":[],"evidence":ev(str(source_path),"migration","Legacy flow omitted actor."),"confidence":"UNVERIFIED"},{"id":"papercompany-system","name":"Papercompany system","type":"system","roles":["LEGACY_SYSTEM"],"entry_points":[],"permissions":[],"evidence":ev(str(source_path),"migration"),"confidence":"DOC_ONLY"}],"domains":domains,"entities":[],"state_machines":[],"business_rules":[],"domain_interactions":[],"business_streams":streams,"visual_outputs":[],"risks":[{"id":"legacy-flow-semantic-loss","severity":"CRITICAL","description":"Legacy output records ordered labels but not actors, triggers, guards, states, errors, or observable outcomes.","mitigation":"Re-run v5 extraction against source code and tests.","evidence":ev(str(source_path),"cross_domain_flows"),"confidence":"VERIFIED"}],"uncertainties":[{"id":"missing-stream-semantics","question":"Who starts each flow, under which rules, and with what state transitions?","impact":"The diagrams cannot be trusted as operational business streams.","resolution":"Use CodeGraph plus routes, policies, schemas, tests, and runtime evidence to rebuild streams.","confidence":"UNVERIFIED"}]}
    report=f"""# Legacy → v5 migration report\n\nSource: `{source_path}`\n\n- Domains migrated: **{len(domains)}**\n- Legacy path summaries migrated as incomplete streams: **{len(streams)}**\n- Actors, triggers, guards, state machines, business rules, errors, retries, and compensation were **not present** in the legacy model and were not invented.\n- Output confidence is `UNVERIFIED`; this file is a re-analysis checklist, not an approved architecture map.\n\n## Required remediation\n\n1. Identify concrete entry points and actors for every critical stream.\n2. Extract authorization, eligibility, and policy guards.\n3. Reconstruct entity state machines and step-level state changes.\n4. Add error, retry, timeout, cancellation, and compensation paths.\n5. Generate child stream/state diagrams, compose a master map, render previews, and run visual QA.\n6. Connect flow, domain, entity, state, rule, codebase, and evidence notes in Obsidian.\n"""
    return model,report

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("legacy_map",type=Path); ap.add_argument("output_dir",type=Path)
    args=ap.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    model,report=migrate(read_json(args.legacy_map),args.legacy_map)
    write_json(args.output_dir/"map-model.v5.migrated.json",model); (args.output_dir/"migration-report.md").write_text(report,encoding="utf-8")
    print(f"WROTE {args.output_dir/'map-model.v5.migrated.json'}"); print(f"WROTE {args.output_dir/'migration-report.md'}"); return 0
if __name__=="__main__": raise SystemExit(main())
