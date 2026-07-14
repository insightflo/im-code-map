#!/usr/bin/env python3
"""Run a clean-room validation of the im-code-map v5 package.

The validator rebuilds the Focus projection and both Excalidraw profiles, renders
previews, regenerates the question-centered and Atlas Obsidian graphs, validates
all machine models and links, and checks that pre-generated examples match the
expected output set. It distrusts decorative success, as any competent validator
should after observing software for more than an afternoon.
"""
from __future__ import annotations

import argparse
import json
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

VERSION = "5.1.0"


def fail(message: str) -> None:
    raise RuntimeError(message)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON {path}: {exc}")


def run(cmd: list[str], *, cwd: Path) -> None:
    # Stream child output directly. Repeatedly capturing large Excalidraw-generation output in
    # pipes can stall long clean-room runs in constrained agent containers, while inheriting the
    # current stdout/stderr preserves the same audit trail without buffering surprises.
    print("RUN:", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=cwd, text=True)
    if result.returncode:
        fail(f"command failed with exit code {result.returncode}: {' '.join(cmd)}")


def require(root: Path, paths: Iterable[str]) -> None:
    missing = [item for item in paths if not (root / item).exists()]
    if missing:
        fail(f"missing required files: {missing}")


def validate_frontmatter(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("SKILL.md is missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        fail("SKILL.md frontmatter is not closed")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    for key in ("name", "description", "version"):
        if not fields.get(key):
            fail(f"SKILL.md frontmatter is missing {key}")
    if fields["name"] != "im-code-map" or fields["version"] != VERSION:
        fail("SKILL.md frontmatter name/version mismatch")
    phrases = [
        "Focus profile, default", "Deep Atlas profile", "understanding-session.json",
        "coverage.json", "evidence-ledger.json", "Raw JSON is not visual QA",
        "6–12 numbered primary-story nodes", "Mandatory Atlas escalation triggers",
        "human-overview.excalidraw", "atlas-master", "validate_human_understanding.py",
        "openwiki code --init", "CodeGraph", "im-code-map-architecture.excalidrawlib",
        "whiteboard", "curated section index",
    ]
    absent = [p for p in phrases if p not in text]
    if absent:
        fail(f"SKILL.md is missing v5 policies: {absent}")
    print("OK: SKILL.md frontmatter and v5 Focus/Atlas policies")


def validate_manifest(root: Path) -> None:
    manifest = read_json(root / "manifest.json")
    if manifest.get("name") != "im-code-map" or manifest.get("version") != VERSION:
        fail("manifest name/version mismatch")
    if manifest.get("default_profile") != "focus":
        fail("manifest default_profile must be focus")
    if not {"focus", "atlas"}.issubset(set(manifest.get("supported_profiles", []))):
        fail("manifest must support focus and atlas")
    if manifest.get("default_documentation_provider") != "agent-native-docs":
        fail("default documentation provider must be agent-native-docs")
    required_tools = set(manifest.get("required_tools_for_normal_mode", []))
    if not {"git", "codegraph", "python3"}.issubset(required_tools):
        fail("normal mode must require git, codegraph, and python3")
    outputs = " ".join(manifest.get("primary_outputs", [])).lower()
    for phrase in ("understanding session", "coverage", "focus", "atlas", "obsidian", "stencil library"):
        if phrase not in outputs:
            fail(f"manifest primary_outputs missing {phrase}")
    if manifest.get("default_visual_theme") != "clean":
        fail("manifest default_visual_theme must be clean")
    if not {"clean", "whiteboard"}.issubset(set(manifest.get("visual_themes", []))):
        fail("manifest visual_themes must include clean and whiteboard")
    if manifest.get("bundled_stencil_library") != "libraries/im-code-map-architecture.excalidrawlib":
        fail("manifest bundled_stencil_library path mismatch")
    print("OK: manifest v5.1 policy")


def validate_json_files(root: Path) -> None:
    count = 0
    for pattern in ("*.json", "*.canvas", "*.excalidraw", "*.excalidrawlib"):
        for path in sorted(root.rglob(pattern)):
            read_json(path); count += 1
    print(f"OK: parsed {count} JSON/Canvas/Excalidraw files")


def validate_clean_tree(root: Path) -> None:
    junk=[]
    for path in root.rglob("*"):
        if path.name in {".DS_Store", "__pycache__"} or path.suffix in {".pyc", ".pyo"}:
            junk.append(path.relative_to(root).as_posix())
    if junk:
        fail(f"package contains transient files: {junk}")
    obsolete=[
        root/"examples/visual-model.example.json",
        root/"examples/excalidraw/master-commerce-map.excalidraw",
        root/"scripts/migrate_v3_to_v4.py",
    ]
    present=[p.relative_to(root).as_posix() for p in obsolete if p.exists()]
    if present:
        fail(f"obsolete v4 package paths remain: {present}")
    print("OK: package tree is clean and obsolete v4 paths are absent")


def compile_scripts(root: Path, temp: Path) -> None:
    temp.mkdir(parents=True, exist_ok=True)
    scripts=sorted((root/"scripts").glob("*.py"))
    for script in scripts:
        try:
            py_compile.compile(str(script), cfile=str(temp/f"{script.stem}.pyc"), doraise=True)
        except py_compile.PyCompileError as exc:
            fail(f"Python compile failed for {script.name}: {exc}")
    print(f"OK: compiled {len(scripts)} Python scripts")


def validate_stencil_library(root: Path) -> None:
    library_path = root / "libraries/im-code-map-architecture.excalidrawlib"
    preview_path = root / "libraries/im-code-map-architecture-preview.excalidraw"
    library = read_json(library_path)
    if library.get("type") != "excalidrawlib" or library.get("version") != 2:
        fail("stencil library root type/version mismatch")
    items = library.get("libraryItems", [])
    if len(items) < 12:
        fail("stencil library contains too few reusable components")
    ids = [item.get("id") for item in items]
    names = [item.get("name") for item in items]
    if None in ids or len(ids) != len(set(ids)) or None in names or len(names) != len(set(names)):
        fail("stencil library item ids/names must be present and unique")
    for item in items:
        elements = item.get("elements", [])
        if not elements:
            fail(f"empty stencil item: {item.get('name')}")
        if any(e.get("type") in {"image", "embeddable"} for e in elements):
            fail(f"stencil item embeds non-native asset: {item.get('name')}")
    preview = read_json(preview_path)
    meta = preview.get("imCodeMap") or {}
    if meta.get("designSystemVersion") != "1.0.0" or meta.get("diagramType") != "stencil-library":
        fail("stencil preview lacks v5.1 design metadata")
    for path in (root / "libraries/previews").glob("*.png"):
        if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            fail(f"invalid stencil preview PNG signature: {path}")
    print(f"OK: package-owned Excalidraw library ({len(items)} stencils)")


def validate_artifact_set(root: Path) -> None:
    focus_ids={"human-overview", "focus-member-place-order"}
    atlas_ids={"domain-commerce-overview", "stream-member-place-order", "state-product-order-eligibility", "stream-browse-orderable-products", "stream-cancel-order", "atlas-master-commerce-map"}
    for profile, expected in (("focus", focus_ids), ("atlas", atlas_ids)):
        drawings={p.stem for p in (root/f"examples/{profile}/excalidraw").glob("*.excalidraw")}
        svgs={p.stem for p in (root/f"examples/{profile}/previews").glob("*.svg")}
        pngs={p.stem for p in (root/f"examples/{profile}/previews").glob("*.png")}
        if drawings != expected or svgs != expected or pngs != expected:
            fail(f"{profile} example artifact set mismatch drawings={drawings} svg={svgs} png={pngs}")
        for png in (root/f"examples/{profile}/previews").glob("*.png"):
            if png.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                fail(f"invalid PNG signature: {png}")
    print("OK: included Focus and Atlas drawings/previews")


def clean_room(root: Path, temp: Path) -> None:
    """Exercise the release pipeline in one shell subprocess.

    Some constrained agent containers become unreliable after a long sequence of
    nested ``subprocess.run`` calls, even though every individual command is fast.
    Running the same audited commands under one fail-fast shell preserves the
    clean-room coverage and avoids turning the validator into a patience benchmark.
    """
    import shlex

    py = Path(sys.executable).resolve()
    ex = root / "examples"
    map_model = ex / "map-model.example.json"
    session = ex / "understanding-session.example.json"
    coverage = ex / "coverage.example.json"
    ledger = ex / "evidence-ledger.example.json"
    focus_bundled = ex / "focus-visual-model.example.json"
    atlas = ex / "atlas-visual-model.example.json"

    generated = temp / "generated"
    architecture = temp / "vault" / "architecture"
    machine = architecture / "machine"
    focus_draw = architecture / "excalidraw"
    focus_prev = architecture / "previews"
    focus_auto = architecture / "excalidraw-automate"
    whiteboard_draw = temp / "whiteboard"
    atlas_draw = architecture / "atlas" / "excalidraw"
    atlas_prev = architecture / "atlas" / "previews"
    atlas_auto = architecture / "atlas" / "excalidraw-automate"
    atlas_sample = temp / "atlas-sample"
    atlas_sample_prev = temp / "atlas-sample-previews"
    master_check = temp / "master-check"
    library_dir = temp / "library"
    generated_library = library_dir / "im-code-map-architecture.excalidrawlib"
    generated_library_preview = library_dir / "im-code-map-architecture-preview.excalidraw"
    focus_regenerated = generated / "focus-visual-model.json"

    q = lambda value: shlex.quote(str(value))
    shell = f"""
set -euo pipefail
PY={q(py)}
ROOT={q(root)}
EX={q(ex)}
TEMP={q(temp)}
GENERATED={q(generated)}
ARCH={q(architecture)}
MACHINE={q(machine)}
FOCUS_DRAW={q(focus_draw)}
FOCUS_PREV={q(focus_prev)}
FOCUS_AUTO={q(focus_auto)}
WHITEBOARD={q(whiteboard_draw)}
ATLAS_DRAW={q(atlas_draw)}
ATLAS_PREV={q(atlas_prev)}
ATLAS_AUTO={q(atlas_auto)}
ATLAS_SAMPLE={q(atlas_sample)}
ATLAS_SAMPLE_PREV={q(atlas_sample_prev)}
MASTER_CHECK={q(master_check)}
LIBRARY_DIR={q(library_dir)}
FOCUS_MODEL={q(focus_regenerated)}

step() {{
  printf 'RUN:'
  printf ' %q' "$@"
  printf '\n'
  "$@"
}}

mkdir -p "$GENERATED" "$MACHINE" "$FOCUS_DRAW" "$FOCUS_PREV" "$FOCUS_AUTO" \
  "$WHITEBOARD" "$ATLAS_DRAW" "$ATLAS_PREV" "$ATLAS_AUTO" \
  "$ATLAS_SAMPLE" "$ATLAS_SAMPLE_PREV" "$MASTER_CHECK" "$LIBRARY_DIR"

step "$PY" "$ROOT/scripts/generate_excalidraw_stencil_library.py" \
  {q(generated_library)} --preview {q(generated_library_preview)}
step "$PY" "$ROOT/scripts/validate_excalidraw_output.py" \
  {q(generated_library_preview)} --strict-warnings
step "$PY" "$ROOT/scripts/render_excalidraw_preview.py" \
  {q(generated_library_preview)} "$LIBRARY_DIR/preview.svg"

step "$PY" "$ROOT/scripts/validate_map_model.py" {q(map_model)} --strict-warnings
step "$PY" "$ROOT/scripts/validate_understanding_session.py" {q(session)} --map-model {q(map_model)}
step "$PY" "$ROOT/scripts/validate_coverage.py" {q(coverage)} --session {q(session)} --strict-warnings
step "$PY" "$ROOT/scripts/validate_evidence_ledger.py" {q(ledger)} --strict-warnings

step "$PY" "$ROOT/scripts/build_focus_profile.py" {q(map_model)} {q(session)} {q(coverage)} "$FOCUS_MODEL"
step "$PY" "$ROOT/scripts/validate_visual_model.py" "$FOCUS_MODEL" --map-model {q(map_model)} --strict-warnings
step "$PY" "$ROOT/scripts/validate_human_understanding.py" "$FOCUS_MODEL" \
  --session {q(session)} --coverage {q(coverage)} --map-model {q(map_model)} --strict-warnings
step "$PY" "$ROOT/scripts/validate_visual_model.py" {q(atlas)} --map-model {q(map_model)} --strict-warnings

step "$PY" "$ROOT/scripts/generate_excalidraw_from_visual_model.py" "$FOCUS_MODEL" "$FOCUS_DRAW"
step "$PY" "$ROOT/scripts/validate_excalidraw_output.py" "$FOCUS_DRAW" --strict-warnings
step "$PY" "$ROOT/scripts/render_excalidraw_preview.py" "$FOCUS_DRAW" "$FOCUS_PREV"
step "$PY" "$ROOT/scripts/generate_excalidraw_automate_scripts.py" "$FOCUS_MODEL" "$FOCUS_AUTO" \
  --vault-folder architecture/excalidraw

step "$PY" "$ROOT/scripts/generate_excalidraw_from_visual_model.py" "$FOCUS_MODEL" "$WHITEBOARD" \
  --diagram focus-member-place-order --theme whiteboard
step "$PY" "$ROOT/scripts/validate_excalidraw_output.py" "$WHITEBOARD" --strict-warnings

step "$PY" "$ROOT/scripts/generate_excalidraw_from_visual_model.py" {q(atlas)} "$ATLAS_SAMPLE" \
  --diagram stream-member-place-order --diagram domain-commerce-overview
step "$PY" "$ROOT/scripts/validate_excalidraw_output.py" "$ATLAS_SAMPLE" --strict-warnings
step "$PY" "$ROOT/scripts/render_excalidraw_preview.py" "$ATLAS_SAMPLE" "$ATLAS_SAMPLE_PREV"

step "$PY" "$ROOT/scripts/compose_excalidraw_master.py" {q(atlas)} \
  "$EX/atlas/excalidraw" "$MASTER_CHECK" --link-prefix architecture/atlas/excalidraw
cp "$EX/atlas/excalidraw/"*.excalidraw "$ATLAS_DRAW/"
cp "$EX/atlas/previews/"*.svg "$ATLAS_PREV/"
step "$PY" "$ROOT/scripts/generate_excalidraw_automate_scripts.py" {q(atlas)} "$ATLAS_AUTO" \
  --vault-folder architecture/atlas/excalidraw

step "$PY" "$ROOT/scripts/generate_focus_obsidian_docs.py" {q(map_model)} "$FOCUS_MODEL" \
  {q(session)} {q(coverage)} "$ARCH"
step "$PY" "$ROOT/scripts/generate_obsidian_docs.py" {q(map_model)} {q(atlas)} "$ARCH/atlas"
step "$PY" "$ROOT/scripts/generate_focus_canvas.py" {q(session)} "$ARCH/understanding-map.canvas" \
  --architecture-prefix architecture
step "$PY" "$ROOT/scripts/generate_workspace_canvas.py" {q(map_model)} {q(atlas)} \
  "$ARCH/atlas/workspace-stream-map.canvas" --architecture-prefix architecture/atlas

cp {q(map_model)} "$MACHINE/map-model.json"
cp {q(session)} "$MACHINE/understanding-session.json"
cp {q(coverage)} "$MACHINE/coverage.json"
cp {q(ledger)} "$MACHINE/evidence-ledger.json"
cp "$FOCUS_MODEL" "$MACHINE/focus-visual-model.json"
cp {q(atlas)} "$MACHINE/atlas-visual-model.json"
step "$PY" "$ROOT/scripts/validate_obsidian_links.py" "$TEMP/vault" --strict-warnings
"""

    print("RUN: clean-room release pipeline (single fail-fast shell)", flush=True)
    result = subprocess.run(["bash", "-lc", shell], cwd=root, text=True)
    if result.returncode:
        fail(f"clean-room release pipeline failed with exit code {result.returncode}")

    if read_json(generated_library) != read_json(root / "libraries/im-code-map-architecture.excalidrawlib"):
        fail("bundled stencil library is not deterministic generator output")
    if read_json(generated_library_preview) != read_json(root / "libraries/im-code-map-architecture-preview.excalidraw"):
        fail("bundled stencil preview is not deterministic generator output")
    if read_json(focus_regenerated) != read_json(focus_bundled):
        fail("bundled Focus visual model is not deterministic output of build_focus_profile.py")

    whiteboard_scene = read_json(whiteboard_draw / "focus-member-place-order.excalidraw")
    if (whiteboard_scene.get("imCodeMap") or {}).get("theme") != "whiteboard":
        fail("whiteboard theme generation metadata mismatch")

    regenerated_master = master_check / "atlas-master-commerce-map.excalidraw"
    bundled_master = root / "examples/atlas/excalidraw/atlas-master-commerce-map.excalidraw"
    if read_json(regenerated_master) != read_json(bundled_master):
        fail("bundled Atlas master is not deterministic compose_excalidraw_master.py output")

    if len(list(focus_draw.glob("*.excalidraw"))) != 2 or len(list(focus_prev.glob("*.svg"))) != 2:
        fail("clean-room Focus output count mismatch")
    if len(list(atlas_sample.glob("*.excalidraw"))) != 2 or len(list(atlas_sample_prev.glob("*.svg"))) != 2:
        fail("clean-room Atlas representative output count mismatch")
    if len(list(atlas_draw.glob("*.excalidraw"))) != 6 or len(list(atlas_prev.glob("*.svg"))) != 6:
        fail("bundled Atlas artifact handoff count mismatch")
    if len(list(architecture.rglob("*.md"))) < 35:
        fail("clean-room Obsidian graph produced too few notes")
    print("OK: clean-room Focus + whiteboard + representative Atlas generation, deterministic master, Obsidian, Canvas, and links")


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("root",nargs="?",type=Path,default=Path(__file__).resolve().parents[1]); a=ap.parse_args(); root=a.root.resolve()
    required=[
      "SKILL.md","README.md","CHANGELOG.md","sources.md","manifest.json",
      "templates/map-model.schema.json","templates/visual-model.schema.json","templates/workspace-registry.schema.json",
      "templates/understanding-session.schema.json","templates/coverage.schema.json","templates/evidence-ledger.schema.json",
      "templates/understanding-session.template.json","templates/coverage.template.json","templates/evidence-ledger.template.json",
      "templates/focus-flow.template.md","templates/start-here.template.md",
      "references/evidence-extraction.md","references/visual-design-rules.md","references/obsidian-linking-rules.md",
      "references/icon-policy.md","references/legacy-migration.md","references/focus-vs-atlas.md",
      "references/human-understanding-quality-gates.md","references/progressive-disclosure.md",
      "references/excalidraw-design-system.md","references/external-library-policy.md","icons/icon-registry.json",
      "reviews/v5.1-visual-design-review.ko.md","reviews/validation-summary.md",
      "templates/excalidraw-design-system.json","libraries/README.md",
      "libraries/im-code-map-architecture.excalidrawlib","libraries/im-code-map-architecture-preview.excalidraw",
      "libraries/previews/im-code-map-architecture-preview.svg","libraries/previews/im-code-map-architecture-preview.png",
      "scripts/excalidraw_design_system.py","scripts/generate_excalidraw_stencil_library.py",
      "examples/map-model.example.json","examples/focus-visual-model.example.json","examples/atlas-visual-model.example.json",
      "examples/understanding-session.example.json","examples/coverage.example.json","examples/evidence-ledger.example.json",
      "examples/workspace-registry.example.json","examples/demo-commerce/source-snapshot.md",
    ]
    try:
        require(root,required); validate_frontmatter(root/"SKILL.md"); validate_manifest(root); validate_clean_tree(root); validate_json_files(root); validate_stencil_library(root); validate_artifact_set(root)
        with tempfile.TemporaryDirectory(prefix="im-code-map-v5-validate-") as tmp:
            temp=Path(tmp); compile_scripts(root,temp/"bytecode"); clean_room(root,temp)
        print(f"PASS: im-code-map v{VERSION} package validated end-to-end"); return 0
    except Exception as exc:
        print(f"FAIL: {exc}",file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
