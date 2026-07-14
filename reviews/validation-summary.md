# im-code-map v5.1.0 validation summary

Validated on 2026-07-14.

## Package contract

- Default profile: `focus`
- Detailed profile: `atlas`
- Default visual theme: `clean`
- Alternate visual theme: `whiteboard`
- Shared factual model: `map-model.json` + `evidence-ledger.json`
- Question and scope: `understanding-session.json` + `coverage.json`
- Detailed output root: `architecture/atlas/`
- Bundled reusable library: `libraries/im-code-map-architecture.excalidrawlib`

## Bundled example

- Business streams: 3
- Focus diagrams: 2
- Atlas child diagrams: 5
- Atlas master diagrams: 1
- Focus PNG/SVG previews: 2 each
- Atlas PNG/SVG previews: 6 each
- Focus ExcalidrawAutomate scripts: 2
- Atlas ExcalidrawAutomate scripts: 4
- Native Excalidraw stencils: 14
- Atlas Canvas: 30 nodes, 40 edges
- Obsidian Markdown notes: 38
- Python scripts: 24
- Parse-checked JSON/Canvas/Excalidraw/Excalidrawlib files: 46

## Validation result

- Map-model validation: PASS, 3 streams, 0 errors, 0 warnings
- Focus visual-model validation: PASS, 2 diagrams, 0 errors, 0 warnings
- Human-understanding structural gates: PASS, 0 errors, 0 warnings
- Focus Excalidraw semantic/readability checks: PASS, 2 files
- Whiteboard theme representative generation: PASS
- Atlas visual-model validation: PASS, 5 child diagrams, 0 errors, 0 warnings
- Bundled Atlas Excalidraw semantic/readability checks: PASS, 6 files including master
- Clean-room Atlas representative generation and SVG rendering: PASS, 2 diagrams
- Deterministic Atlas master recomposition: PASS
- Package-owned stencil regeneration and preview: PASS, 14 items
- Obsidian, Canvas, and drawing link validation: PASS, 0 errors, 0 warnings
- Deterministic Focus regeneration: PASS
- Clean-room package validation: PASS

The example contains a payment risk boundary. Focus is permitted for explanation, but Atlas is required before changing or approving payment, timeout, idempotency, or compensation behavior. The single routing warning is intentional rather than a validation failure.

## Visual release boundary

The package contains no third-party icon artwork, vendor logos, external SVGs, or copied `.excalidrawlib` items. The bundled library is generated from native Excalidraw primitives owned by this package. External collections remain optional references and require exact-asset license review before import.

## Legacy limitation

`701. Papercompany.zip` contains generated architecture material only. It does not contain the application source repository or tests. Legacy migration therefore preserves labels and ordering as `UNVERIFIED`; it does not certify runtime behavior or invent missing actors, guards, states, errors, retries, or compensation.
