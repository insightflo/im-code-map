# Foglamp map-generation comparison

Reference snapshot: `foglamp-labs/foglamp@0021f51d09a7d6910cc4e36f9eabaabc1d31e568`.

## Patterns adopted independently

- A bounded overview contract forces prioritization before layout.
- The semantic model does not contain coordinates, colors, or icon choices.
- A deterministic renderer owns layout and visual vocabulary.
- Sequential stages become compact groups; groups flow left-to-right.
- Model/tool/rule/evidence leaves can be folded into the card that uses them.
- Cross-group edges are deduplicated for the overview; detailed edges remain in Atlas.
- Labels have strict budgets and edge labels sit on open channel segments.
- A deep pipeline opens at its beginning rather than shrinking every label below readability.

## Deliberately not adopted

- Foglamp's AI-only node vocabulary is not sufficient for general codebases.
- The 24-node limit applies only to Overview/Focus, never to the evidence ledger or Deep Atlas.
- No public upload, favicon dependency, hosted renderer, or edit token is required.
- Evidence, confidence, unknowns, states, errors, compensation, and source links remain first-class.
- No Foglamp source code or visual assets are bundled. The implementation is independent.

## Resulting pipeline

```text
repository evidence
→ detailed semantic model
→ bounded map projection
→ fixed clean renderer
→ Excalidraw / SVG / PNG
→ linked Obsidian detail and Deep Atlas
```
