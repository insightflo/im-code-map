#!/usr/bin/env python3
"""Validate Obsidian wiki links, embeds, Canvas file nodes, and Excalidraw links."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

WIKI = re.compile(r"!?\[\[([^\]]+)\]\]")


def candidates_for(target: str, current: Path, vault: Path) -> list[Path]:
    target = target.strip().split("|", 1)[0].split("#", 1)[0].strip()
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return []
    raw = Path(target)
    bases = [current.parent / raw, vault / raw]
    result: list[Path] = []
    for base in bases:
        result.append(base)
        if not base.suffix:
            result.extend(base.with_suffix(ext) for ext in (".md", ".canvas", ".excalidraw"))
    return result


def resolve(target: str, current: Path, vault: Path, suffix_index: dict[str, list[Path]]) -> bool:
    clean = target.strip().split("|", 1)[0].split("#", 1)[0].strip()
    if not clean or clean.startswith(("http://", "https://", "mailto:")):
        return True
    for candidate in candidates_for(target, current, vault):
        try:
            candidate.resolve().relative_to(vault.resolve())
        except ValueError:
            continue
        if candidate.exists():
            return True
    # Obsidian commonly stores shortest unique suffixes instead of vault-root absolute paths.
    normalized = clean.replace("\\", "/").lstrip("./")
    variants = {normalized}
    if not Path(normalized).suffix:
        variants.update(normalized + ext for ext in (".md", ".canvas", ".excalidraw"))
    for variant in variants:
        matches = suffix_index.get(variant, [])
        if len(matches) == 1:
            return True
    return False


def iter_links_in_excalidraw(path: Path) -> Iterable[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    links = []
    for element in data.get("elements", []):
        if element.get("link"):
            links.append(str(element["link"]))
        if element.get("type") == "text":
            links.extend(m.group(1) for m in WIKI.finditer(str(element.get("text", ""))))
    return links


def validate(vault: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    files = [p for p in vault.rglob("*") if p.is_file()]
    suffix_index: dict[str, list[Path]] = defaultdict(list)
    for p in files:
        rel = p.relative_to(vault).as_posix()
        suffix_index[rel].append(p)
        parts = rel.split("/")
        for i in range(1, len(parts)):
            suffix_index["/".join(parts[i:])].append(p)
        suffix_index[p.name].append(p)
        suffix_index[p.stem].append(p)

    for path in files:
        rel = path.relative_to(vault).as_posix()
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            for match in WIKI.finditer(text):
                target = match.group(1)
                if not resolve(target, path, vault, suffix_index):
                    errors.append(f"{rel}: unresolved wiki link [[{target}]]")
        elif path.suffix == ".canvas":
            try:
                canvas = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"{rel}: invalid Canvas JSON: {exc}")
                continue
            node_ids = {n.get("id") for n in canvas.get("nodes", [])}
            for n in canvas.get("nodes", []):
                if n.get("type") == "file":
                    target = str(n.get("file", ""))
                    if not (vault / target).exists():
                        errors.append(f"{rel}: Canvas file node missing target {target}")
            for e in canvas.get("edges", []):
                if e.get("fromNode") not in node_ids or e.get("toNode") not in node_ids:
                    errors.append(f"{rel}: Canvas edge {e.get('id')} references missing node")
        elif path.suffix == ".excalidraw":
            for raw in iter_links_in_excalidraw(path):
                targets = [m.group(1) for m in WIKI.finditer(raw)] or [raw]
                for target in targets:
                    if not resolve(target, path, vault, suffix_index):
                        warnings.append(f"{rel}: unresolved Excalidraw link {target}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vault_root", type=Path)
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()
    errors, warnings = validate(args.vault_root)
    for item in warnings: print(f"WARN: {item}")
    for item in errors: print(f"FAIL: {item}")
    if not errors:
        print(f"PASS: Obsidian wiki, Canvas, and drawing links under {args.vault_root}")
    print(f"SUMMARY errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors or (args.strict_warnings and warnings) else 0

if __name__ == "__main__":
    raise SystemExit(main())
