#!/usr/bin/env python3
"""Validate the v5 evidence ledger and its claim/source traceability."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
from im_code_map_common import read_json

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("ledger",type=Path); ap.add_argument("--schema",type=Path); ap.add_argument("--strict-warnings",action="store_true")
    a=ap.parse_args(); data=read_json(a.ledger); schema=read_json(a.schema or Path(__file__).resolve().parents[1]/"templates/evidence-ledger.schema.json")
    errors=[]; warnings=[]
    try:
        from jsonschema import Draft202012Validator
        errors += [f"schema {'.'.join(map(str,e.absolute_path)) or '<root>'}: {e.message}" for e in sorted(Draft202012Validator(schema).iter_errors(data),key=lambda e:list(e.absolute_path))]
    except Exception:
        warnings.append("jsonschema is not installed; structural schema validation skipped")
    seen=set()
    for claim in data.get("claims",[]):
        cid=claim.get("id")
        if cid in seen: errors.append(f"duplicate claim id {cid}")
        seen.add(cid)
        if claim.get("confidence") in {"VERIFIED","PARTIAL","DOC_ONLY"} and not claim.get("supports"):
            errors.append(f"claim {cid} has confidence {claim.get('confidence')} but no support")
        if claim.get("confidence")=="CONFLICT" and not claim.get("contradictions"):
            errors.append(f"claim {cid} is CONFLICT but contradictions are empty")
        if not claim.get("used_by"): warnings.append(f"claim {cid} is not used by any session, stream, or diagram")
    for x in warnings: print("WARN:",x)
    for x in errors: print("FAIL:",x)
    if not errors: print(f"PASS: evidence ledger claims={len(data.get('claims',[]))}")
    print(f"SUMMARY errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors or (a.strict_warnings and warnings) else 0
if __name__=='__main__': raise SystemExit(main())
