#!/usr/bin/env python3
"""Validate a v5 understanding session and its Focus/Atlas routing decision."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
from im_code_map_common import read_json

HIGH_RISK = {
    "authentication", "authorization", "payment", "privacy", "data-deletion", "migration",
    "concurrency", "idempotency", "retry-compensation", "cross-repository",
    "conflicting-evidence", "dynamic-dispatch", "broad-state-change",
}


def schema_errors(data: dict[str, Any], schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except Exception:
        return ["jsonschema is not installed; structural schema validation skipped"]
    schema=read_json(schema_path)
    return [f"schema {'.'.join(map(str,e.absolute_path)) or '<root>'}: {e.message}" for e in sorted(Draft202012Validator(schema).iter_errors(data),key=lambda e:list(e.absolute_path))]


def validate(data: dict[str, Any], map_model: dict[str, Any] | None=None) -> tuple[list[str],list[str]]:
    errors=[]; warnings=[]
    routing=data.get("routing_decision",{})
    risk=data.get("risk_assessment",{})
    selected=routing.get("selected_profile")
    triggers=set(risk.get("triggers",[]))
    if risk.get("requires_atlas") and selected=="focus":
        # An understanding-only Focus is allowed, but it must not pretend to approve a risky change.
        if data.get("intent") in {"before-change","debug","atlas"}:
            errors.append("risk_assessment requires Atlas for this change/debug intent, but routing selected Focus")
        else:
            warnings.append("high-risk boundary is summarized in Focus; Atlas is required before changing or approving it")
    if triggers & HIGH_RISK and not risk.get("requires_atlas"):
        errors.append(f"high-risk triggers must set requires_atlas=true: {sorted(triggers & HIGH_RISK)}")
    if routing.get("automatic_escalation") and selected!="atlas":
        errors.append("automatic_escalation=true requires selected_profile=atlas")
    if data.get("requested_depth")=="atlas" and selected!="atlas":
        errors.append("requested_depth=atlas must route to Atlas")
    if data.get("intent")=="atlas" and selected!="atlas":
        errors.append("intent=atlas must route to Atlas")
    if map_model is not None:
        stream_id=data.get("selected_stream_id")
        stream_ids={s.get("id") for s in map_model.get("business_streams",[])}
        if data.get("intent") in {"trace","explain","before-change","debug","expand"} and not stream_id:
            errors.append(f"intent={data.get('intent')} requires selected_stream_id")
        if stream_id and stream_id not in stream_ids:
            errors.append(f"selected_stream_id does not exist in map-model: {stream_id}")
    if not data.get("scope",{}).get("in_scope"):
        errors.append("scope.in_scope must not be empty")
    if len(data.get("question","").strip()) < 5:
        errors.append("question is too short to define a useful understanding session")
    return errors,warnings


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("session",type=Path); ap.add_argument("--map-model",type=Path); ap.add_argument("--schema",type=Path); ap.add_argument("--strict-warnings",action="store_true")
    a=ap.parse_args(); data=read_json(a.session); schema=a.schema or Path(__file__).resolve().parents[1]/"templates/understanding-session.schema.json"
    se=schema_errors(data,schema); warnings=[x for x in se if x.startswith("jsonschema")]; errors=[x for x in se if not x.startswith("jsonschema")]
    e,w=validate(data,read_json(a.map_model) if a.map_model else None); errors+=e; warnings+=w
    for x in warnings: print("WARN:",x)
    for x in errors: print("FAIL:",x)
    if not errors: print(f"PASS: understanding session {data.get('session_id')} routed to {data.get('routing_decision',{}).get('selected_profile')}")
    print(f"SUMMARY errors={len(errors)} warnings={len(warnings)}")
    strict_warnings=[x for x in warnings if not x.startswith("jsonschema")]
    return 1 if errors or (a.strict_warnings and strict_warnings) else 0
if __name__=='__main__': raise SystemExit(main())
