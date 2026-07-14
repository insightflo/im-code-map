#!/usr/bin/env python3
"""Validate an immutable remote repository snapshot used as normal-mode evidence."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from im_code_map_common import read_json

SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
CORE_CLASSES = {"route", "service", "test", "schema"}


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
    snapshot = data.get("snapshot", {})
    commit = str(snapshot.get("commit_sha", ""))
    if not SHA40.fullmatch(commit):
        errors.append("snapshot.commit_sha must be a full 40-character commit SHA")

    acquisition = data.get("acquisition", {})
    if acquisition.get("mode") not in {"remote-connector-snapshot", "hybrid"}:
        errors.append("snapshot acquisition mode must be remote-connector-snapshot or hybrid")
    contract = acquisition.get("content_contract", {})
    for key in ("immutable_ref", "blob_sha_per_file", "line_ranges", "no_unfetched_claims"):
        if contract.get(key) is not True:
            errors.append(f"acquisition.content_contract.{key} must be true")

    paths: set[str] = set()
    classes: set[str] = set()
    for item in data.get("files", []):
        path = str(item.get("path", ""))
        if path in paths:
            errors.append(f"duplicate snapshot file path: {path}")
        paths.add(path)
        if item.get("ref") != commit:
            errors.append(f"snapshot file {path} is not pinned to snapshot.commit_sha")
        if not SHA40.fullmatch(str(item.get("blob_sha", ""))):
            errors.append(f"snapshot file {path} lacks a full blob SHA")
        classes.add(str(item.get("evidence_class", "")))
        last_end = 0
        for idx, line_range in enumerate(item.get("line_ranges", []), start=1):
            start = line_range.get("start")
            end = line_range.get("end")
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
                errors.append(f"snapshot file {path} range {idx} is invalid")
                continue
            if start < last_end:
                warnings.append(f"snapshot file {path} ranges overlap or are out of order")
            last_end = max(last_end, end)
            if not str(line_range.get("excerpt", "")).strip():
                errors.append(f"snapshot file {path} range {idx} has no excerpt")

    coverage = data.get("coverage", {})
    if coverage.get("fetched_file_count") != len(paths):
        errors.append("coverage.fetched_file_count does not match files length")
    declared_classes = set(coverage.get("evidence_classes", []))
    if declared_classes != classes:
        errors.append("coverage.evidence_classes does not match classes present in files")
    missing_core = CORE_CLASSES - classes
    if missing_core:
        warnings.append(f"remote snapshot lacks core evidence classes: {sorted(missing_core)}")
    if not coverage.get("cross_checks"):
        warnings.append("remote snapshot has no cross-class claim check")
    for check in coverage.get("cross_checks", []):
        check_classes = set(check.get("classes", []))
        if len(check_classes) < 2:
            errors.append(f"cross-check {check.get('claim')} uses fewer than two evidence classes")
        unknown = check_classes - classes
        if unknown:
            errors.append(f"cross-check {check.get('claim')} references absent classes {sorted(unknown)}")

    integrity = data.get("integrity", {})
    if integrity.get("result") == "PASS" and (errors or missing_core):
        errors.append("integrity.result cannot be PASS when snapshot validation is incomplete")
    if integrity.get("immutable_ref") is not True or integrity.get("all_files_pinned") is not True:
        errors.append("snapshot integrity must assert immutable_ref and all_files_pinned")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--schema", type=Path, default=None)
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()
    data = read_json(args.snapshot)
    schema = args.schema or Path(__file__).resolve().parents[1] / "templates" / "repository-snapshot.schema.json"
    raw = schema_errors(data, schema)
    warnings = [message for message in raw if message.startswith("jsonschema")]
    errors = [message for message in raw if not message.startswith("jsonschema")]
    semantic_errors, semantic_warnings = validate(data)
    errors.extend(semantic_errors)
    warnings.extend(semantic_warnings)
    for message in warnings:
        print(f"WARN: {message}")
    for message in errors:
        print(f"FAIL: {message}")
    if not errors:
        print(f"PASS: immutable repository snapshot ({len(data.get('files', []))} files, commit={data.get('snapshot', {}).get('commit_sha')})")
    print(f"SUMMARY errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors or (args.strict_warnings and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
