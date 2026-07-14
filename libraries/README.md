# im-code-map Excalidraw library

`im-code-map-architecture.excalidrawlib` contains the reusable visual components used by the v5.1 generator.

## Included stencils

- actor;
- service;
- Focus decision card;
- Atlas decision diamond;
- state transition;
- event;
- data store;
- queue;
- external system;
- risk or unknown boundary;
- compensation;
- observable outcome;
- domain;
- Deep Atlas link.

All items are built from native Excalidraw primitives authored in this package. No third-party logos, icon packs, emoji, fonts, or copied library elements are embedded.

## Regenerate

```bash
python scripts/generate_excalidraw_stencil_library.py
python scripts/render_excalidraw_preview.py \
  libraries/im-code-map-architecture-preview.excalidraw \
  libraries/previews/im-code-map-architecture-preview.svg \
  --png
```

## Import into Obsidian Excalidraw

Open the Excalidraw library menu and import `im-code-map-architecture.excalidrawlib`. The same stencils can then be placed manually while retaining the visual grammar used by generated drawings.
