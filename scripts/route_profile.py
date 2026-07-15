#!/usr/bin/env python3
"""Report the v5 Focus/Atlas routing decision and any mandatory escalation boundary."""
from __future__ import annotations
import argparse
from pathlib import Path
from im_code_map_common import read_json
from validate_understanding_session import validate


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("session",type=Path); ap.add_argument("--map-model",type=Path)
    a=ap.parse_args(); session=read_json(a.session); model=read_json(a.map_model) if a.map_model else None
    errors,warnings=validate(session,model)
    decision=session.get("routing_decision",{}); risk=session.get("risk_assessment",{})
    print(f"PROFILE={decision.get('selected_profile','UNKNOWN')}")
    print(f"INTENT={session.get('intent','UNKNOWN')}")
    print(f"RISK={risk.get('level','UNKNOWN')}")
    print(f"REQUIRES_ATLAS={str(bool(risk.get('requires_atlas'))).lower()}")
    print(f"REASON={decision.get('reason','')}")
    for item in warnings: print(f"WARN={item}")
    for item in errors: print(f"ERROR={item}")
    return 1 if errors else 0
if __name__=='__main__': raise SystemExit(main())
