#!/usr/bin/env python3
"""Validate v5 explored, unknown, out-of-scope, and expansion coverage."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
from im_code_map_common import read_json

def schema_errors(data:dict[str,Any],schema_path:Path)->list[str]:
    try:
        from jsonschema import Draft202012Validator
    except Exception:
        return ["jsonschema is not installed; structural schema validation skipped"]
    schema=read_json(schema_path)
    return [f"schema {'.'.join(map(str,e.absolute_path)) or '<root>'}: {e.message}" for e in sorted(Draft202012Validator(schema).iter_errors(data),key=lambda e:list(e.absolute_path))]

def validate(data:dict[str,Any],session:dict[str,Any]|None=None)->tuple[list[str],list[str]]:
    errors=[]; warnings=[]; ids={}
    for group in ("explored","unknown_relevant","unknown_out_of_scope","expansion_points"):
        for item in data.get(group,[]):
            iid=item.get("id")
            if iid in ids: errors.append(f"duplicate coverage id {iid} in {group} and {ids[iid]}")
            ids[iid]=group
            if item.get("impact") in {"blocks-answer","blocks-change","relevant-later"} and not item.get("next_check") and group!="explored":
                errors.append(f"{group} item {iid} needs next_check")
            if group=="unknown_out_of_scope" and item.get("impact")!="none-for-current-purpose":
                warnings.append(f"out-of-scope item {iid} has impact {item.get('impact')}; reconsider whether it is truly out of scope")
    completion=data.get("completion",{})
    blocking=[x for x in data.get("unknown_relevant",[]) if x.get("impact")=="blocks-answer"]
    if completion.get("question_answered") and blocking:
        errors.append(f"question_answered=true but relevant unknowns still block the answer: {[x['id'] for x in blocking]}")
    if completion.get("safe_to_change")=="yes" and any(x.get("impact")=="blocks-change" for x in data.get("unknown_relevant",[])):
        errors.append("safe_to_change=yes conflicts with unknown_relevant items that block change")
    if session and data.get("session_id")!=session.get("session_id"):
        errors.append("coverage session_id does not match understanding session")
    if not data.get("explored"): errors.append("coverage must record at least one explored area")
    return errors,warnings

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("coverage",type=Path); ap.add_argument("--session",type=Path); ap.add_argument("--schema",type=Path); ap.add_argument("--strict-warnings",action="store_true")
    a=ap.parse_args(); data=read_json(a.coverage); schema=a.schema or Path(__file__).resolve().parents[1]/"templates/coverage.schema.json"
    se=schema_errors(data,schema); warnings=[x for x in se if x.startswith("jsonschema")]; errors=[x for x in se if not x.startswith("jsonschema")]
    e,w=validate(data,read_json(a.session) if a.session else None); errors+=e; warnings+=w
    for x in warnings: print("WARN:",x)
    for x in errors: print("FAIL:",x)
    if not errors: print(f"PASS: coverage explored={len(data.get('explored',[]))} relevant_unknowns={len(data.get('unknown_relevant',[]))} out_of_scope={len(data.get('unknown_out_of_scope',[]))}")
    print(f"SUMMARY errors={len(errors)} warnings={len(warnings)}")
    strict_warnings=[x for x in warnings if not x.startswith("jsonschema")]
    return 1 if errors or (a.strict_warnings and strict_warnings) else 0
if __name__=='__main__': raise SystemExit(main())
