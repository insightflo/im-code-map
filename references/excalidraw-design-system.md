# Excalidraw design system in v5.1

## Why v5.0 looked generated instead of designed

The v5.0 diagrams were semantically valid, but the first view gave equal visual weight to raw note links, frames, card text, lane labels, and arrows. Small pictograms sat inside large boxes, decisions were forced into text-heavy diamonds, and the Atlas master shrank complete child drawings until they became technically present and practically unreadable.

v5.1 separates **information architecture** from **drawing decoration**. Every visual element must help the reader answer one of four questions:

1. Where do I start?
2. What is the main path?
3. Where does the path branch, stop, or cross a system boundary?
4. Where can I open deeper evidence?

## Default visual language

- Clean presentation theme by default: sans-serif text, solid fills, low roughness, restrained shadows.
- Optional `whiteboard` theme: Excalidraw hand-drawn character without changing the layout grammar.
- Large title and purpose header, followed by compact navigation buttons rather than raw wiki paths.
- Reusable component cards with an icon tile, semantic accent, title, short explanation, and an independent numbered step badge.
- Decisions use readable rule cards in Focus. Diamonds remain available in detailed Atlas views when compact predicates are useful.
- Happy-path arrows are dominant. Error, retry, async, data, and compensation connectors have distinct color and line styles.
- Edge labels sit on white label pills instead of floating over lines.
- Focus uses vertical phase storyboards. It never reverses the reading direction merely to fit a snake layout.
- Atlas uses visible system/lane boundaries, but boundary boxes remain quieter than the runtime flow.
- The master canvas includes a readable index and preserves full child drawings without pretending that a tiny thumbnail is a detailed map.

## Stencil library

`libraries/im-code-map-architecture.excalidrawlib` is generated from primitives owned by this package. It contains reusable cards for actor, service, decision, state, event, data store, external system, risk, compensation, and navigation patterns. The same visual components are used by the deterministic generator.

Generate it with:

```bash
python scripts/generate_excalidraw_stencil_library.py \
  libraries/im-code-map-architecture.excalidrawlib
```

## External references and license boundary

The following resources were studied for layout and reuse patterns:

- Excalidraw public Libraries directory: reusable library workflow and component browsing.
- `karanpratapsingh/system-design`: concise architecture components and importable library workflow.
- `aretecode/system-design-templates-excalidraw`: grouped stencil-sheet workflow and rapid copy/paste.
- `Prakash-sa/system-design-ultimatum`: topic-organized drawings, shared components, and generated previews.
- `swaymun/system-design-excalidraws`: practical system-design diagrams and component reuse.
- `Bowen-0x00/obsidian-excalidraw-example-vault`: Obsidian-oriented scripts and preconfigured canvas examples.

No third-party drawing, icon, or library asset is bundled by v5.1. Some referenced repositories either credit other sources or do not expose a repository-wide license clearly enough for redistribution. They are treated as visual research only. Optional third-party imports must pass the license gate described in `references/external-library-policy.md`.
