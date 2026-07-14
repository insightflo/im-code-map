#!/usr/bin/env python3
"""Validate map-model v5 schema, shared evidence references, and Atlas stream completeness."""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from im_code_map_common import VALID_CONFIDENCE, ensure_unique_ids, read_json


def schema_errors(data: dict[str, Any], schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except Exception:
        return ["jsonschema is not installed; structural schema validation skipped"]
    schema = read_json(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.absolute_path))
    return [f"schema {'.'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors]


def validate(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    profile_support = data.get("profile_support", {})
    if profile_support.get("default_profile") != "focus":
        errors.append("map-model v5 default_profile must be focus")
    supported = set(profile_support.get("supported_profiles", []))
    if not {"focus", "atlas"}.issubset(supported):
        errors.append("map-model v5 must support both focus and atlas profiles")
    if not profile_support.get("atlas_escalation_triggers"):
        errors.append("map-model v5 must declare Atlas escalation triggers")

    collections = {
        "codebase": data.get("codebases", []), "actor": data.get("actors", []),
        "domain": data.get("domains", []), "entity": data.get("entities", []),
        "state_machine": data.get("state_machines", []), "business_rule": data.get("business_rules", []),
        "domain_interaction": data.get("domain_interactions", []), "business_stream": data.get("business_streams", []),
    }
    for label, items in collections.items():
        duplicates = ensure_unique_ids(items, label)
        if duplicates:
            errors.append(f"duplicate {label} ids: {duplicates}")
        for item in items:
            if item.get("confidence") not in VALID_CONFIDENCE:
                errors.append(f"{label} {item.get('id')} has invalid confidence")
            if "evidence" in item and not item.get("evidence"):
                warnings.append(f"{label} {item.get('id')} has no evidence")

    codebase_ids = {x["id"] for x in collections["codebase"]}
    actor_ids = {x["id"] for x in collections["actor"]}
    domain_ids = {x["id"] for x in collections["domain"]}
    entity_ids = {x["id"] for x in collections["entity"]}
    state_ids = {x["id"] for x in collections["state_machine"]}
    rule_ids = {x["id"] for x in collections["business_rule"]}
    stream_ids = {x["id"] for x in collections["business_stream"]}
    entity_by_id = {x["id"]: x for x in collections["entity"]}
    state_by_id = {x["id"]: x for x in collections["state_machine"]}

    for domain in collections["domain"]:
        for cb in domain.get("implementations_by_codebase", {}):
            if cb not in codebase_ids:
                errors.append(f"domain {domain['id']} references unknown codebase {cb}")
        for entity in domain.get("owned_entities", []):
            if entity not in entity_ids:
                errors.append(f"domain {domain['id']} owns unknown entity {entity}")
        for state in domain.get("owned_state_machines", []):
            if state not in state_ids:
                errors.append(f"domain {domain['id']} owns unknown state machine {state}")
        for stream in domain.get("participating_streams", []):
            if stream not in stream_ids:
                errors.append(f"domain {domain['id']} references unknown stream {stream}")
        if domain.get("type") == "business" and not domain.get("participating_streams"):
            message = f"business domain {domain['id']} is not connected to any business stream"
            if data.get("confidence") == "UNVERIFIED":
                warnings.append(message)
            else:
                errors.append(message)

    for entity in collections["entity"]:
        if entity.get("domain_id") not in domain_ids:
            errors.append(f"entity {entity['id']} references unknown domain {entity.get('domain_id')}")
        for rule in entity.get("eligibility_rules", []):
            if rule not in rule_ids:
                errors.append(f"entity {entity['id']} references unknown rule {rule}")
        sm = entity.get("state_machine_id")
        if sm and sm not in state_ids:
            errors.append(f"entity {entity['id']} references unknown state machine {sm}")

    for machine in collections["state_machine"]:
        entity_id = machine.get("entity_id")
        if entity_id not in entity_ids:
            errors.append(f"state machine {machine['id']} references unknown entity {entity_id}")
            continue
        states = {s["id"] for s in machine.get("states", [])}
        if machine.get("initial_state") not in states:
            errors.append(f"state machine {machine['id']} initial state is not declared")
        for transition in machine.get("transitions", []):
            if transition.get("from") not in states or transition.get("to") not in states:
                errors.append(f"state transition {transition.get('id')} references unknown state")
            if not transition.get("trigger"):
                errors.append(f"state transition {transition.get('id')} has no trigger")
            if not transition.get("guard"):
                warnings.append(f"state transition {transition.get('id')} has an empty guard; use 'none' explicitly")

    for rule in collections["business_rule"]:
        for stream in rule.get("used_by_streams", []):
            if stream not in stream_ids:
                errors.append(f"rule {rule['id']} references unknown stream {stream}")
        if not rule.get("condition") or not rule.get("outcome"):
            errors.append(f"rule {rule['id']} must state both condition and outcome")

    for interaction in collections["domain_interaction"]:
        if interaction.get("from_domain") not in domain_ids or interaction.get("to_domain") not in domain_ids:
            errors.append(f"interaction {interaction['id']} references unknown domain")
        if not interaction.get("contract"):
            errors.append(f"interaction {interaction['id']} has no contract")
        for stream in interaction.get("used_by_streams", []):
            if stream not in stream_ids:
                errors.append(f"interaction {interaction['id']} references unknown stream {stream}")

    if len(collections["business_stream"]) < 1:
        errors.append("at least one business stream is required")
    elif len(collections["business_stream"]) < 3 and len(domain_ids) >= 5:
        warnings.append("fewer than three business streams cover a non-trivial domain model; verify critical journeys are not omitted")

    for stream in collections["business_stream"]:
        sid = stream["id"]
        for actor in stream.get("actor_ids", []):
            if actor not in actor_ids:
                errors.append(f"stream {sid} references unknown actor {actor}")
        for domain in stream.get("domain_ids", []):
            if domain not in domain_ids:
                errors.append(f"stream {sid} references unknown domain {domain}")
        if not stream.get("trigger", {}).get("entry_point"):
            errors.append(f"stream {sid} has no concrete entry point")
        steps = stream.get("steps", [])
        step_dupes = ensure_unique_ids(steps, f"stream {sid} step")
        if step_dupes:
            errors.append(f"stream {sid} duplicate step ids: {step_dupes}")
        step_by_id = {s["id"]: s for s in steps}
        start_id = stream.get("start_step_id")
        if start_id not in step_by_id:
            errors.append(f"stream {sid} start_step_id does not exist")
            continue
        if step_by_id[start_id].get("kind") != "start":
            errors.append(f"stream {sid} start_step_id is not kind=start")
        end_ids = {s["id"] for s in steps if s.get("kind") == "end"}
        if not end_ids:
            errors.append(f"stream {sid} has no kind=end step")

        outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
        incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for transition in stream.get("transitions", []):
            fr, to = transition.get("from"), transition.get("to")
            if fr not in step_by_id or to not in step_by_id:
                errors.append(f"stream {sid} transition {transition.get('id')} references unknown step")
                continue
            outgoing[fr].append(transition)
            incoming[to].append(transition)
            if transition.get("kind") in {"conditional", "error", "timeout", "retry", "compensation", "cancel"} and not str(transition.get("condition", "")).strip():
                errors.append(f"stream {sid} transition {transition.get('id')} needs a condition")

        for step in steps:
            step_id = step["id"]
            if step.get("actor_id") not in actor_ids:
                errors.append(f"stream {sid} step {step_id} references unknown actor")
            if step.get("domain_id") not in domain_ids:
                errors.append(f"stream {sid} step {step_id} references unknown domain")
            for rule in step.get("rule_refs", []):
                if rule not in rule_ids:
                    errors.append(f"stream {sid} step {step_id} references unknown rule {rule}")
            for change in step.get("state_changes", []):
                entity_id = change.get("entity_id")
                if entity_id not in entity_ids:
                    errors.append(f"stream {sid} step {step_id} changes unknown entity {entity_id}")
                    continue
                machine_id = entity_by_id[entity_id].get("state_machine_id")
                known_states = set()
                if machine_id in state_by_id:
                    known_states = {s["id"] for s in state_by_id[machine_id].get("states", [])}
                for state_key in ("from", "to"):
                    value = change.get(state_key)
                    if known_states and value not in known_states and value not in {"NONE", "ANY", "?"}:
                        errors.append(f"stream {sid} step {step_id} uses unknown {entity_id} state {value}")
            if step.get("kind") == "decision":
                branches = outgoing.get(step_id, [])
                if len(branches) < 2:
                    errors.append(f"stream {sid} decision {step_id} has fewer than two branches")
                for branch in branches:
                    if not branch.get("condition"):
                        errors.append(f"stream {sid} decision branch {branch.get('id')} lacks condition")
            if step.get("kind") == "end" and outgoing.get(step_id):
                errors.append(f"stream {sid} terminal step {step_id} has outgoing transitions")
            if step_id != start_id and not incoming.get(step_id):
                errors.append(f"stream {sid} step {step_id} is unreachable: no incoming transition")

        # Graph reachability from trigger to all modeled work.
        reached = {start_id}
        queue = deque([start_id])
        while queue:
            current = queue.popleft()
            for transition in outgoing.get(current, []):
                nxt = transition["to"]
                if nxt not in reached:
                    reached.add(nxt)
                    queue.append(nxt)
        missing = set(step_by_id) - reached
        if missing:
            errors.append(f"stream {sid} unreachable steps from start: {sorted(missing)}")

        outcome_ids = set()
        for outcome in stream.get("outcomes", []):
            if outcome.get("id") in outcome_ids:
                errors.append(f"stream {sid} duplicate outcome id {outcome.get('id')}")
            outcome_ids.add(outcome.get("id"))
            terminal = outcome.get("terminal_step_id")
            if terminal not in end_ids:
                errors.append(f"stream {sid} outcome {outcome.get('id')} does not target an end step")
            if not outcome.get("observable_result"):
                errors.append(f"stream {sid} outcome {outcome.get('id')} lacks observable_result")
        if end_ids - {o.get("terminal_step_id") for o in stream.get("outcomes", [])}:
            errors.append(f"stream {sid} has terminal steps without declared outcomes")

        for error_path in stream.get("error_paths", []):
            for key in ("from_step_id", "handler_step_id"):
                if error_path.get(key) not in step_by_id:
                    errors.append(f"stream {sid} error path {error_path.get('id')} references unknown {key}")
            if error_path.get("terminal_outcome_id") not in outcome_ids:
                errors.append(f"stream {sid} error path {error_path.get('id')} references unknown outcome")
        if any(s.get("kind") == "external-call" for s in steps) and not stream.get("error_paths"):
            warnings.append(f"stream {sid} has an external call but no explicit error path")
        if not stream.get("diagram_paths"):
            errors.append(f"stream {sid} has no diagram path")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_model", type=Path)
    parser.add_argument("--schema", type=Path, default=None)
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()
    data = read_json(args.map_model)
    schema = args.schema or Path(__file__).resolve().parents[1] / "templates" / "map-model.schema.json"
    s_errors = schema_errors(data, schema)
    # Missing jsonschema is a warning; actual schema failures are errors.
    warnings = [x for x in s_errors if x.startswith("jsonschema")]
    errors = [x for x in s_errors if not x.startswith("jsonschema")]
    semantic_errors, semantic_warnings = validate(data)
    errors.extend(semantic_errors)
    warnings.extend(semantic_warnings)
    for message in warnings:
        print(f"WARN: {message}")
    for message in errors:
        print(f"FAIL: {message}")
    if not errors:
        print(f"PASS: map-model schema and stream semantics ({len(data.get('business_streams', []))} streams)")
    print(f"SUMMARY errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors or (args.strict_warnings and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
