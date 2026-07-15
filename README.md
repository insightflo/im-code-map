# im-code-map v5.3.1

`im-code-map` now defaults to **human understanding**, not maximum diagram coverage.

The skill keeps one evidence model and exposes it through two profiles:

- **Focus** answers one explicit question with a readable central flow, visible uncertainty, and links into deeper evidence.
- **Deep Atlas** preserves the detailed streams, states, rules, failures, compensation, domains, code references, and infinite-canvas composition introduced in v4.

## Why v5

A complete map can be technically correct and still fail its purpose because a reader cannot tell where to start. v5 adds a question, stop condition, coverage boundary, reader contract, and progressive detail path. It does not erase complexity. It delays complexity until the reader needs it, an astonishingly controversial concession to the finite human brain.


## v5.1 visual system

v5.1 keeps the Focus/Atlas evidence model from v5.0 and replaces the old generator-looking presentation with a shared Excalidraw design system:

- `clean` is the default presentation theme; `whiteboard` keeps Excalidraw roughness without changing layout semantics.
- Focus uses three left-to-right phase rows, numbered cards, quiet happy-path arrows, visible stop reasons, and compact note buttons.
- Atlas uses subdued boundaries, readable swimlanes, system component cards, explicit conditional branches, and a curated infinite-canvas index.
- `libraries/im-code-map-architecture.excalidrawlib` contains 14 package-owned reusable stencils built only from native Excalidraw primitives.
- external template repositories are references, not copied dependencies, unless an exact asset passes the license gate.

## v5.3.1 multilingual preview fix

The clean overview renderer now performs a local font-coverage preflight before creating SVG/PNG previews. Korean and other CJK text uses a deterministic fallback stack led by `Noto Sans CJK KR`; if no installed font covers the required glyphs, preview generation fails with an actionable message instead of silently producing square boxes. Font files are never bundled.

Numbered Focus steps also use small external badges so long Korean labels no longer collide with step numbers.

## Output structure

```text
architecture/
  start-here.md
  visual-index.md
  understanding-map.canvas
  understanding/
  flows/
  unknowns.md
  excalidraw/
    human-overview.excalidraw
    focus-<stream>.excalidraw
  previews/
  atlas/
    index.md
    start-here.md
    workspace-stream-map.canvas
    flows/ actors/ domains/ entities/ states/ rules/ codebases/
    excalidraw/
      atlas-master-*.excalidraw
    previews/
  machine/
    understanding-session.json
    coverage.json
    evidence-ledger.json
    map-model.json
    focus-visual-model.json
    atlas-visual-model.json
```

## Bundled example

The synthetic commerce example asks:

> 회원이 상품을 주문하면 어떤 처리가 시작되고, 무엇을 확인한 뒤 주문이 완료되는가?

The Focus drawing shows three numbered, left-to-right semantic phase rows, summarized stop reasons, one relevant unknown, and the Deep Atlas progression. The Atlas preserves all detailed branches, states, errors, and compensation.

## Validate the package

```bash
python scripts/validate_skill_package.py .
```

The validator rebuilds both profiles in a temporary clean-room directory, renders previews, regenerates the Obsidian graph and Canvas, checks links, and runs the human-understanding gate.

## Requirements

Normal mode requires Git, CodeGraph, Python 3.10+, and a writable output directory. Clean multilingual preview validation additionally uses `fonttools`; PNG rendering uses CairoSVG when available and Pillow as a fallback. A Korean-capable local font such as Noto Sans CJK KR or NanumGothic is required when the map contains Korean. Obsidian, Excalidraw plugins, ExcalidrawAutomate, and OpenWiki are optional viewers/editors.

## License note

No third-party icon artwork is bundled. Icons and the included `.excalidrawlib` are generated from package-owned native Excalidraw primitives. External tools and optional libraries retain their own licenses and must be reviewed separately.
