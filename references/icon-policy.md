# Icon policy

## Bundled assets

The package bundles only:

- native Excalidraw primitive shapes;
- text labels generated from the evidence model;
- `libraries/im-code-map-architecture.excalidrawlib`, generated from those same package-owned primitives.

No third-party icon font, SVG pack, PNG pack, or `.excalidrawlib` artwork is included.

## Why

Visual familiarity is useful, but redistribution rights are not implied by popularity, a public URL, or the fact that an icon can be copied. Decorative enthusiasm is not a license review.

## External library intake checklist

Before bundling any external item, record:

- project/library name;
- canonical source URL;
- author or publisher;
- license identifier and license text location;
- attribution requirement;
- whether modification is allowed;
- whether redistribution inside this package is allowed;
- exact item IDs/names used;
- date checked;
- reviewer decision.

If any field cannot be confirmed, do not bundle the asset. A user may still load their own local library at runtime under their own license obligations.

## Accessibility

- Icons accompany text; they never replace it.
- Shape and edge labels preserve meaning without color.
- Use high-contrast semantic styles.
- Do not use emoji as semantic icons; use native vector primitives whose geometry is stable across platforms.
