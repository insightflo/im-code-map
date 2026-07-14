# Excalidraw visual design rules

## 1. Two profiles, one evidence model

Focus and Atlas are different projections of the same `map-model.json` and evidence ledger.

- Focus prioritizes one reader question and a central story.
- Atlas exposes full stream, state, rule, failure, compensation, domain, and implementation context.

Never maintain two independent factual models.

## 2. Focus first-view layout

Required regions:

```text
START HERE · central story
Why the flow stops
Still unknown / current boundary
Open Deep Atlas
```

The primary story is numbered and normally contains 6–12 nodes. Keep no more than four cards per row and no more than four decisions visible. Wrap longer stories into numbered semantic phase rows. Every row reads left-to-right; a routed connector in the gap moves the reader to the first card of the next phase. Use a separate summary card for non-success branches.

Focus uses human action and business meaning. Implementation identifiers belong in linked notes.

## 3. Atlas layout

Atlas business streams use actor/system lanes. Long flows are divided into semantic phase frames. A frame should normally remain below 18 nodes.

Suggested phase vocabulary:

1. request and authorization;
2. eligibility and selection;
3. creation and reservation;
4. external processing;
5. completion and publication;
6. rejection, failure, and compensation.


## 3.1 Presentation theme

The generator uses `templates/excalidraw-design-system.json`.

- `clean` is the default: sans-serif text, solid fill, low roughness, quiet shadows, and restrained semantic color.
- `whiteboard` changes font family and roughness while preserving the same information hierarchy and layout.
- raw `[[wiki/path]]` text is never shown in a Focus drawing; linked note buttons use human labels.
- edges are rendered behind semantic cards; vector icons and labels remain above cards.

A theme may change appearance, never branch meaning, evidence, or reading order.

## 4. Semantic grammar

| Meaning | Shape | Required text |
|---|---|---|
| start/end/actor | semantic card or compact ellipse | initiator or observable result |
| process/action | rounded rectangle | action verb + object |
| decision | Focus rule card; Atlas diamond | business question or predicate |
| state change | state card | human meaning and, in Atlas, `before → after` |
| data/store | data/storage card | read or write purpose |
| event/wait | event/wait card | sync/async meaning |
| external call | external card | provider/system + operation |
| error | error card | failure and effect |
| compensation | compensation card | undo/release/refund action |
| boundary/unknown | note or risk card | what is unknown and why it matters |

Icons are recognition aids, not substitutes for labels.

## 5. Edge semantics

Atlas edges state why processing continues and expose all branches. Focus keeps ordinary sequence arrows unlabeled, places the rule inside each decision card, and uses only short selected-branch cues. It summarizes the remaining branches.

Examples:

```text
verified member
ACTIVE and sale window open
available quantity is sufficient
payment authorized
published asynchronously
```

Color and line style reinforce meaning but never carry it alone.

## 6. Text budget

Focus:

- numbered label plus concise human summary;
- uncertainty summarized in the boundary region rather than stamped on every card;
- no raw UUID, route, symbol chain, or database trivia in first view;
- implementation detail in linked Atlas note.

Atlas:

- short action label;
- normally no more than 28 words in card summary;
- long rules and evidence in linked notes.

Minimum rendered font is 12 px. Smaller text is not decomposition. It is surrender with typography.

## 7. Child and master composition

Canonical Atlas child files:

- one critical stream per drawing;
- state/eligibility views where behavior depends on lifecycle state;
- domain responsibility and typed contract view;
- optional error, sequence, data-lifecycle, and impact views.

The Atlas master composes children into labeled regions and links to each child.

Focus drawings remain separate projections:

- `human-overview.excalidraw`;
- `focus-<stream>.excalidraw`.


## 7.1 Package-owned stencil library

The package includes `libraries/im-code-map-architecture.excalidrawlib` and a rendered catalog. It provides actor, service, decision-card, decision-diamond, state, event, storage, queue, external, risk, compensation, outcome, domain, and Atlas-link components.

The deterministic generator and the manual stencil library share the same visual tokens. Do not substitute unrelated public icons merely to make a drawing more decorative. External items must pass `references/external-library-policy.md`.

## 8. Mandatory render review

Render and inspect:

- human overview;
- selected Focus flow;
- Atlas master;
- one state/eligibility drawing;
- one error or compensation-heavy Atlas flow.

Fail or revise when the start is hard to find, the central story competes with error branches, unknowns are hidden, the path to Atlas is unclear, branch conditions are missing, text overlaps, or the master becomes a wall of duplicated text.
