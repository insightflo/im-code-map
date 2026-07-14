# External Excalidraw library policy

## Default rule

Do not copy a third-party `.excalidraw`, `.excalidrawlib`, SVG, PNG, logo, or icon into a generated package merely because it is publicly visible.

## Import gate

An external component may be bundled only when all conditions are met:

1. the exact asset has a license that permits redistribution and modification;
2. required attribution and license text are included;
3. trademarked vendor logos are not presented as generic architecture semantics;
4. the asset does not embed unrelated source material or paid components;
5. the generated diagram still works when the optional library is absent.

## Safe default

Use the package-owned `im-code-map-architecture.excalidrawlib`. Treat external libraries as optional user-installed resources. Record their name, source, version or commit, license, and imported component identifiers in the visual review report.
