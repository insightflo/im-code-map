#!/usr/bin/env python3
"""Validate whether a v5 Focus projection is actually readable by a person.

This is a structural proxy, not a claim that a script can measure comprehension.
It enforces the reader contract, first-view limits, progressive disclosure links,
visible boundaries, and traceability back to the shared stream model.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path
from typing import Any
from im_code_map_common import read_json

OPAQUE = [
    re.compile(r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b", re.I),
    re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){2,}\b"),
    re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+/"),
]

def validate(visual:dict[str,Any], session:dict[str,Any], coverage:dict[str,Any], map_model:dict[str,Any])->tuple[list[str],list[str]]:
    errors=[]; warnings=[]
    if visual.get("profile")!="focus": errors.append("human understanding validator requires profile=focus")
    policy=visual.get("reader_policy",{})
    if policy.get("detail_policy")!="progressive-disclosure": errors.append("Focus must use progressive-disclosure")
    if policy.get("implementation_identifiers")=="visible": errors.append("Focus must hide implementation identifiers or keep them in notes")
    if int(policy.get("first_view_target_seconds",999))>60: warnings.append("Focus first_view_target_seconds exceeds 60 seconds")
    diagrams=visual.get("diagrams",[]); by_type={}
    for d in diagrams: by_type.setdefault(d.get("type"),[]).append(d)
    if not by_type.get("human-overview"): errors.append("Focus output requires a human-overview diagram")
    if not by_type.get("focus-flow"): errors.append("Focus output requires at least one focus-flow diagram")
    stream_ids={s["id"] for s in map_model.get("business_streams",[])}
    selected=session.get("selected_stream_id")
    if selected not in stream_ids: errors.append(f"selected stream missing from map-model: {selected}")
    relevant_unknowns={x["label"] for x in coverage.get("unknown_relevant",[])}
    for d in diagrams:
        did=d.get("id"); nodes={n["id"]:n for n in d.get("nodes",[])}; rc=d.get("reader_contract",{})
        if d.get("profile")!="focus": errors.append(f"diagram {did} profile must be focus")
        start=rc.get("start_here_node_id")
        if start not in nodes: errors.append(f"diagram {did} reader_contract start_here_node_id is missing")
        primary=rc.get("primary_story_node_ids",[])
        missing=[x for x in primary if x not in nodes]
        if missing: errors.append(f"diagram {did} primary_story_node_ids missing nodes: {missing}")
        answers=rc.get("answers",{})
        for key in ("who_starts","what_they_want","key_decisions","success_change"):
            if not str(answers.get(key,"")).strip(): errors.append(f"diagram {did} reader answer {key} is empty")
        if not rc.get("does_not_answer"): errors.append(f"diagram {did} must state what it does not answer")
        for n in nodes.values():
            if n.get("role") in {"primary-story","decision"} and not n.get("details_link"):
                warnings.append(f"diagram {did} story node {n['id']} has no deeper details_link")
            visible=f"{n.get('label','')} {n.get('summary','')}"
            if n.get("role") in {"primary-story","decision"}:
                for pat in OPAQUE:
                    if pat.search(visible): warnings.append(f"diagram {did} node {n['id']} may expose an implementation identifier")
        if d.get("type")=="focus-flow":
            max_story=int(policy.get("max_primary_story_nodes",12))
            if len(primary)<6: warnings.append(f"focus-flow {did} has fewer than 6 primary story nodes; verify it is not too abstract")
            if len(primary)>max_story: errors.append(f"focus-flow {did} has {len(primary)} primary nodes; max is {max_story}")
            roles=[nodes[x].get("role") for x in primary if x in nodes]
            decisions=sum(1 for r in roles if r=="decision")
            if decisions>4: errors.append(f"focus-flow {did} has {decisions} visible decisions; max is 4")
            if not any(nodes[x].get("kind")=="start" for x in primary if x in nodes): errors.append(f"focus-flow {did} primary story has no start")
            if not any(nodes[x].get("kind")=="end" for x in primary if x in nodes): errors.append(f"focus-flow {did} primary story has no success end")
            numbers=[nodes[x].get("step_number") for x in primary if x in nodes]
            if numbers!=list(range(1,len(primary)+1)): errors.append(f"focus-flow {did} step numbers must be contiguous from 1")
            if not any(n.get("role")=="failure-summary" for n in nodes.values()): errors.append(f"focus-flow {did} needs a failure-summary node")
            if not any(n.get("role")=="atlas-link" for n in nodes.values()): errors.append(f"focus-flow {did} needs an Atlas link")
            shown_unknowns=" ".join(n.get("summary","") for n in nodes.values() if n.get("role")=="unknown")
            for label in relevant_unknowns:
                if label not in shown_unknowns: errors.append(f"focus-flow {did} does not expose relevant unknown: {label}")
            collapsed={r for n in nodes.values() for r in n.get("collapsed_refs",[])}
            if collapsed and not rc.get("deeper_links"): errors.append(f"focus-flow {did} collapses detail but has no deeper links")
        if d.get("type")=="human-overview":
            if len(primary)>6: errors.append("human-overview should contain at most 6 first-view nodes")
            if not any(n.get("role")=="atlas-link" for n in nodes.values()): errors.append("human-overview needs a visible Atlas progression")
    return errors,warnings

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("focus_visual",type=Path); ap.add_argument("--session",type=Path,required=True); ap.add_argument("--coverage",type=Path,required=True); ap.add_argument("--map-model",type=Path,required=True); ap.add_argument("--strict-warnings",action="store_true")
    a=ap.parse_args(); e,w=validate(read_json(a.focus_visual),read_json(a.session),read_json(a.coverage),read_json(a.map_model))
    for x in w: print("WARN:",x)
    for x in e: print("FAIL:",x)
    if not e: print("PASS: Focus reader contract, first-view limits, unknown boundaries, and progressive detail")
    print(f"SUMMARY errors={len(e)} warnings={len(w)}")
    return 1 if e or (a.strict_warnings and w) else 0
if __name__=='__main__': raise SystemExit(main())
