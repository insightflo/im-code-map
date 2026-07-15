# Clean Excalidraw map design

## Visual hierarchy

1. Canvas background: quiet off-white.
2. Group containers: low-contrast neutral surface, thin border, no decorative frame chrome.
3. Structural edges: neutral gray; semantic color is reserved for conditional, async, error, data, and recovery paths.
4. Node cards: white, compact, consistent width, small semantic accent stripe and line icon.
5. Text: one title, one short supporting line, optional inline capability chips.

## Default geometry

- 20/24 px rhythm; 220 px node card; 72–96 px height.
- 2–6 nodes per vertical group.
- Groups are ordered left-to-right.
- Orthogonal edges use rounded corners and do not pass through cards.
- Edge labels are placed on the longest free segment and receive a white pill background.
- Recovery/back edges route below the main story.

## Information rules

- Overview cards never display raw UUIDs, long symbols, or full paths.
- File paths and evidence live in `detail`, `evidenceRefs`, and linked notes.
- Fold up to four model/tool/rule/state/evidence/technology leaves into their owner card.
- The overview must show one readable start-to-outcome path.
- Detail is expanded through linked child drawings, not by shrinking the overview.
