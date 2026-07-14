# Changelog

## 5.1.0 — 2026-07-14

### Excalidraw presentation redesign

- Added a versioned `clean` design system with an optional `whiteboard` theme.
- Replaced the Focus snake path with three numbered phase rows that always read left-to-right.
- Added larger semantic icon tiles, independent step badges, restrained shadows, compact navigation buttons, and visible scope/boundary panels.
- Kept Focus decisions as readable rule cards; Atlas decisions remain explicit diamonds with fully labeled branches.
- Reworked Atlas into quiet ownership lanes and system-component cards, including a hub-and-spoke domain responsibility view.
- Replaced coordinate-only master composition with a curated section index and balanced infinite-canvas grid.
- Changed preview z-order so runtime edges sit behind cards and labels instead of cutting through prose.

### Reusable components and licensing

- Added `libraries/im-code-map-architecture.excalidrawlib` with 14 package-owned native-vector stencils.
- Added a visual stencil catalog and deterministic library generator.
- Added an external-library license gate; referenced GitHub collections are visual research only unless exact assets have verified redistribution rights.

### Validation

- Added design-system metadata checks, raw wiki-link leakage checks, Focus reading-path checks, curated-master checks, and library format validation.
- Extended clean-room validation to regenerate the stencil library and its preview.

## 5.0.0 — 2026-07-14

### Breaking behavior change

- Changed the default from full architecture mapping to the `focus` profile.
- Preserved the v4 detailed behavior as the `atlas` profile.
- Added explicit profile routing and mandatory Atlas escalation boundaries.

### Human-understanding model

- Added `understanding-session.json` with question, audience, intent, scope, stop condition, risk, and routing decision.
- Added `coverage.json` with explored areas, relevant unknowns, out-of-scope areas, expansion points, boundaries, and completion status.
- Added `evidence-ledger.json` so simplified cards remain traceable to claims and sources.
- Added reader contracts to every visual diagram.

### Focus visuals and Obsidian

- Added `human-overview` and `focus-flow` diagram types.
- Added numbered first-view stories, visible success, summarized stop reasons, explicit unknowns, and Deep Atlas links.
- Wrapped longer Focus stories into four-card semantic phase rows. v5.1 later replaced the alternating snake direction with consistent left-to-right phase rows.
- Suppressed repetitive per-card confidence badges in Focus; uncertainty is explained once at the visible boundary and retained in the evidence model.
- Rendered Korean preview text with an available CJK-capable system font without bundling font files.
- Added question-centered Obsidian start pages and a compact Focus JSON Canvas.
- Kept Atlas child-to-master infinite-canvas composition.

### Validation

- Added session, coverage, evidence-ledger, and human-understanding validators.
- Added first-view node/decision limits, step-number checks, unknown visibility, progressive-detail checks, and Focus-to-Atlas traceability.
- Expanded clean-room package validation to rebuild both profiles.

### Migration

- Added v4→v5 migration scaffolding with detailed output paths normalized below `architecture/atlas/`.
- Added direct v3→v5 legacy migration with explicit `UNVERIFIED` semantics.

## 4.0.0 — 2026-07-10

- Introduced evidence-first business streams, actors, rules, states, failures, compensation, child Excalidraw files, Atlas master composition, render-based visual QA, and linked Obsidian outputs.
