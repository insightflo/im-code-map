---
name: im-code-map
description: Human-first, evidence-grounded codebase understanding. Defaults to a question-scoped Focus map, preserves a full Deep Atlas, and supports either local CodeGraph analysis or immutable remote repository snapshots. Generates progressive Excalidraw views, linked Obsidian notes, machine-readable evidence, explicit unknowns, and render-based visual QA.
version: 5.2.0
---

# im-code-map v5.2.0

## 1. Mission

Help a person understand enough of a codebase for a concrete purpose without pretending that every subsystem must fit in one mind or one canvas.

The default result is not a complete architecture encyclopedia. It is a verified answer to one useful question:

```text
Who or what starts this behavior?
→ What are they trying to accomplish?
→ Which decisions matter?
→ What data or state changes?
→ What result can the person or system observe?
→ What remains unknown, out of scope, or risky enough to require deeper analysis?
```

The skill keeps two profiles over the same evidence:

- **Focus**: the default human reading path for orientation, one flow, one error, one change, or one operational question.
- **Deep Atlas**: the detailed architecture and runtime model for risky changes, cross-domain reasoning, takeover, audit, incident analysis, migration, or explicit full-map requests.

Do not create separate “simple” and “detailed” truths. Focus is a projection of the shared evidence model; Atlas is a wider projection of that same model.

## 2. Core operating principle

### 2.1 One flow before the whole city

Start from a concrete actor intent, request, event, schedule, command, message, failure, or change. Trace it to an observable end. Expand only when the current question, uncertainty, or risk crosses a boundary.

A domain relationship such as:

```text
Member → Product → Order
```

is context, not an explanation. A useful flow states who the member is, what they request, which product and member conditions permit the action, which state changes occur, and how success or rejection becomes observable.

### 2.2 Partial understanding must be bounded, not disguised

Record three different kinds of missing knowledge:

1. `unknown_relevant`: missing knowledge that blocks the answer or a safe change;
2. `unknown_out_of_scope`: knowledge deliberately excluded from the present purpose;
3. `expansion_points`: useful next flows or boundaries that may be opened later.

Never replace any of these with a plausible story.

### 2.3 Child files are canonical

Maintain detailed stream, state, context, and error diagrams as child Excalidraw files. Compose Atlas masters from those children. Focus diagrams are separate human projections that link to the child sources; they are not flattened copies of the master.

### 2.4 Raw JSON is not visual QA

Every delivery follows:

```text
extract evidence
→ model
→ validate
→ generate
→ render SVG/PNG
→ inspect first-view readability
→ refine
→ re-render
```

A valid `.excalidraw` JSON file can still be an unreadable wall of arrows, a venerable software-documentation tradition that v5 declines to continue.

## 3. Profiles

## 3.1 Focus profile, default

Use Focus for:

- initial orientation;
- “how does this feature work?”;
- one user journey or operational trigger;
- one error or incident path;
- preparing a bounded low-risk change;
- explaining the system to a newcomer or non-specialist;
- expanding one adjacent concern from an earlier Focus session.

Focus answers the current question and exposes the boundary of the answer. It does not claim full codebase coverage.

### Focus first-view contract

A Focus flow should normally contain:

- 6–12 numbered primary-story nodes;
- no more than four cards per row; wrap longer stories into numbered semantic phase rows that always read left-to-right;
- no more than four visible decisions;
- one obvious `START HERE` point;
- one visible success result;
- a central happy path;
- one summarized “why the flow stops” card rather than every failure branch;
- one visible unknown/boundary card when relevant unknowns exist;
- one visible path into Deep Atlas;
- human business language on cards;
- implementation identifiers in linked notes, not on the first-view story.

The diagram must let a reader answer within about 30 seconds:

```text
Who starts?
What do they want?
What are the key decisions?
What changes on success?
```

### Focus is not permission to omit risk

When a risky concern appears in a Focus explanation, show it as a boundary and link to Atlas. A Focus explanation may say “payment approval happens here”; it must not approve a payment change without tracing timeout, idempotency, compensation, state, tests, and runtime evidence.

## 3.2 Deep Atlas profile

Use Atlas when explicitly requested or when the work requires complete branch and impact reasoning.

Atlas includes:

- critical business streams;
- actors, roles, permissions, and entry points;
- business rules and eligibility;
- entity state machines;
- reads, writes, commands, queries, events, queues, jobs, and external calls;
- success, rejection, error, timeout, retry, cancellation, partial success, and compensation;
- domain ownership and typed contracts;
- source, test, schema, configuration, CodeGraph, and runtime evidence;
- child Excalidraw files;
- composed infinite-canvas Atlas master;
- linked Obsidian knowledge graph and Canvas.

Atlas remains detailed, but it still requires an explicit reading order and links back to Focus views. The master must use a curated section index and balanced grid; merely shrinking every child into unreadable thumbnails does not count as composition.

## 4. Routing and escalation

Create `architecture/machine/understanding-session.json` before drawing.

Record:

- the exact question;
- intent;
- audience;
- requested depth;
- selected stream, when known;
- expected answer;
- stop condition;
- in-scope and out-of-scope boundaries;
- risk triggers;
- routing decision and reason.

### 4.1 Default routing

```text
orient / trace / explain / expand → Focus
before-change / debug → Focus only when the relevant boundary is low risk and evidenced
atlas / takeover / audit / migration / broad incident → Atlas
```

### 4.2 Mandatory Atlas escalation triggers

Escalate before approving or implementing work involving any material combination of:

```text
authentication
Authorization or permissions
payment
privacy or personal data
data deletion
migration
concurrency
idempotency
retry and compensation
cross-repository effects
conflicting evidence
dynamic dispatch that breaks the trace
broad state changes
explicit user request for the full map
```

A Focus explanation may still be generated for orientation, but its coverage file must state that Atlas is required before change approval.

Run:

```bash
python scripts/validate_understanding_session.py \
  architecture/machine/understanding-session.json \
  --map-model architecture/machine/map-model.json

python scripts/route_profile.py \
  architecture/machine/understanding-session.json \
  --map-model architecture/machine/map-model.json
```

## 5. Tool policy

### 5.1 Normal evidence modes

Normal mode is defined by evidence integrity, not by whether the repository happens to be mounted locally. Choose exactly one acquisition mode and record it in `tool_status.evidence_mode`.

#### A. `local-codegraph`

Required:

- Git
- CodeGraph CLI
- Python 3.10+
- writable architecture output directory

CodeGraph is the structure and impact evidence source in this mode. Initialize it at the repository or multi-repository workspace root, never at a home directory merely to make the command stop complaining.

Recommended commands:

```bash
git --version
codegraph version
codegraph status
codegraph explore "how does <user-visible behavior> work"
codegraph query <symbol> --json
codegraph callers <symbol> --json
codegraph callees <symbol> --json
codegraph impact <symbol> --json
python3 --version
```

Use `explore` to discover the end-to-end candidate, then focused JSON commands to establish traceable structure evidence.

#### B. `remote-connector-snapshot`

Use this when a repository connector can read repository metadata and file contents but a local checkout or CodeGraph is unavailable.

Required:

- repository identity and default branch from the connector;
- a full immutable commit SHA resolved before analysis;
- every fetched file read at that exact SHA;
- a blob SHA for every fetched file;
- exact line ranges and short excerpts for every material claim;
- route/service/test/schema cross-checks where those evidence classes exist;
- `architecture/machine/repository-snapshot.json` passing `validate_repository_snapshot.py`;
- Python 3.10+ and a writable output directory.

In this mode CodeGraph is `NOT_REQUIRED`, not `BLOCKED`. The connector snapshot is normal evidence only while all claims stay inside fetched content. Repository search results, filenames, commit messages, README prose, and generated docs are discovery aids until the underlying file content is fetched at the pinned SHA.

Do not infer an unfetched caller, callee, runtime branch, or state transition merely because a name suggests one. Put the unresolved edge in `coverage.json` instead.

#### C. `hybrid`

Use a pinned connector snapshot together with a local checkout or CodeGraph. The commit identities must match. Any mismatch is `CONFLICT` until resolved.

See `references/remote-snapshot-mode.md`.

### 5.2 Documentation provider

Default:

```text
agent-native-docs
```

The current agent writes the notes from source, tests, routes, schemas, configuration, runtime evidence, and CodeGraph output.

Optional:

```text
openwiki-cli
```

OpenWiki is never a hidden dependency. When selected, initialize repository mode explicitly with:

```bash
openwiki code --init
```

### 5.3 Optional viewers and editors

- Obsidian
- Obsidian Excalidraw plugin
- ExcalidrawAutomate Script Engine

The package must still produce raw Markdown, JSON Canvas, `.excalidraw`, SVG, and PNG without those viewers.

## 6. Preflight gate

Write:

```text
architecture/machine/tool-preflight-report.md
architecture/machine/workspace-registry.json
```

Check:

- repository and workspace roots;
- nested repositories and packages;
- generated/vendor paths to exclude;
- existing `.codegraph/` scope and freshness;
- writable output path;
- optional viewer availability;
- stale architecture artifacts that could be mistaken for current evidence.

If CodeGraph is unavailable:

1. check whether `remote-connector-snapshot` can meet the immutable-ref, blob-SHA, line-range, and cross-check contract;
2. if it can, continue in normal remote snapshot mode and mark CodeGraph `NOT_REQUIRED`;
3. if it cannot, stop normal mode and state the exact missing evidence capability;
4. continue only under explicit degraded authorization;
5. mark affected claims `PARTIAL` or `UNVERIFIED`;
6. do not use recursive text search as a pretend call graph.

The preflight report must state which evidence mode was selected and why. A network failure during `git clone` is not itself evidence degradation when the connector can still produce a valid immutable snapshot. Conversely, a connector that exposes only repository names or search snippets is not enough for normal mode.

## 7. Shared evidence layer

The profiles share these machine files:

```text
architecture/machine/
  tool-preflight-report.md
  workspace-registry.json
  repository-snapshot.json   # remote/hybrid mode; null/not applicable in local mode
  codegraph-evidence.json    # local/hybrid mode
  evidence-ledger.json
  map-model.json
  understanding-session.json
  coverage.json
  focus-visual-model.json
  atlas-visual-model.json
```

### 7.0 Repository snapshot integrity

For remote or hybrid evidence, run:

```bash
python scripts/validate_repository_snapshot.py \
  architecture/machine/repository-snapshot.json \
  --strict-warnings
```

The snapshot is an acquisition ledger, not a substitute for the semantic map. It proves which immutable files were actually inspected and which claims remain outside coverage.

### 7.1 Confidence

Use only:

- `VERIFIED`: supported by executable source, test, schema, route, configuration, or runtime evidence;
- `PARTIAL`: a material link remains unresolved;
- `DOC_ONLY`: supported only by prose or comments;
- `UNVERIFIED`: migrated, plausible, or not yet evidenced;
- `CONFLICT`: reliable sources disagree.

### 7.2 Evidence ledger

`evidence-ledger.json` stores claims separately from diagrams.

Each claim records:

- claim text;
- confidence;
- supporting sources and locators;
- contradictions;
- sessions, streams, rules, states, or diagrams that use it.

This prevents a simplified card from becoming a new unsourced fact.

Validate:

```bash
python scripts/validate_evidence_ledger.py architecture/machine/evidence-ledger.json
```

## 8. Shared map model

Write `map-model.json` against `templates/map-model.schema.json`.

The model retains the v4 stream semantics and adds profile support. It includes:

- codebases;
- actors;
- domains;
- entities;
- state machines;
- business rules;
- typed domain interactions;
- business streams;
- risks and uncertainties;
- Focus/Atlas support and escalation triggers.

### 8.1 Actors

Capture human, system, schedule, worker, external, and agent actors. Record role/member type, entry point, permissions, evidence, and confidence.

### 8.2 Business streams

Derive streams from observable work, not by connecting domain names.

For each stream record:

- actor intent or system trigger;
- concrete entry point;
- preconditions;
- ordered steps;
- reads and writes;
- rules;
- state changes;
- external and asynchronous boundaries;
- labeled transitions;
- terminal outcomes;
- error/retry/timeout/cancel/compensation behavior;
- evidence and confidence;
- note and diagram paths.

Atlas stream completeness still requires every modeled branch to terminate. Focus may collapse branches only after the full stream remains traceable in the shared model.

### 8.3 State and rules

Do not write merely `Product → Orderable`. Record the evidenced condition, for example:

```text
product.status == ACTIVE
AND saleStartsAt <= now < saleEndsAt
AND availableQty >= requestedQty
```

Only record that expression when a reliable source proves it.

## 9. Coverage model

Write `coverage.json` against `templates/coverage.schema.json`.

The coverage record is part of the answer, not an apology appended after it.

Required sections:

```text
explored
unknown_relevant
unknown_out_of_scope
expansion_points
boundaries
completion
```

A relevant unknown must include its impact and the next check. An out-of-scope item must explain why it does not affect the present purpose. A Focus answer cannot be marked complete while an `unknown_relevant` item still has `impact = blocks-answer`.

Validate:

```bash
python scripts/validate_coverage.py \
  architecture/machine/coverage.json \
  --session architecture/machine/understanding-session.json
```

## 10. Focus generation

Build the Focus visual projection from the shared stream model:

```bash
python scripts/build_focus_profile.py \
  architecture/machine/map-model.json \
  architecture/machine/understanding-session.json \
  architecture/machine/coverage.json \
  architecture/machine/focus-visual-model.json
```

The builder:

- finds the selected success path;
- preserves start, end, decisions, state changes, external calls, and meaningful work;
- keeps the primary story within the first-view node budget;
- wraps long first views into four-card semantic phase lanes so the path remains readable without microscopic zoom;
- records omitted steps in `collapsed_refs`;
- summarizes non-success branches;
- displays relevant unknowns;
- provides explicit Deep Atlas links.

It must preserve the user’s major language in human labels. Source identifiers remain available in linked notes.

## 11. Excalidraw design

Use `templates/excalidraw-design-system.json` for every generated drawing. The default `clean` theme uses solid fills, low roughness, sans-serif text, restrained shadows, and quiet boundaries. The optional `whiteboard` theme may change roughness and font family but must preserve the same semantic hierarchy and layout.

Generate the reusable package-owned library when initializing visual assets:

```bash
python scripts/generate_excalidraw_stencil_library.py \
  libraries/im-code-map-architecture.excalidrawlib \
  --preview libraries/im-code-map-architecture-preview.excalidraw
```

Do not copy third-party `.excalidrawlib`, SVG, logo, or diagram elements into the package unless the exact asset passes `references/external-library-policy.md`. Public visibility is not redistribution permission, a distinction the internet routinely treats as optional.

## 11.1 Focus diagrams

Generate at least:

```text
human-overview.excalidraw
focus-<stream>.excalidraw
```

`human-overview` shows:

```text
START HERE
→ current question
→ selected Focus flow
→ current evidence boundary
→ Deep Atlas
```

A Focus flow shows the central story first. When the story exceeds four cards, wrap it into numbered semantic phase rows. Every phase reads left-to-right; route the transition to the next phase through the whitespace between panels rather than reversing direction. Failure branches are summarized in a separate region. Relevant unknowns and Atlas progression remain visible without competing with the happy path.

Use native vector pictograms from `icons/icon-registry.json`; do not rely on emoji fonts or bundled third-party artwork.

## 11.2 Atlas diagrams

Generate:

- one child per critical business stream;
- state/eligibility children when state controls behavior;
- domain responsibility and contract context;
- selected error, data-lifecycle, sequence, or change-impact children;
- one composed `atlas-master-*.excalidraw` infinite canvas.

Child files are canonical. The master is a regenerated view with links back to each child.

## 11.3 Semantic grammar

| Meaning | Shape/icon role |
|---|---|
| actor, start, end | ellipse / actor-start-end icon |
| action/process | rounded card / process icon |
| decision | diamond / decision icon |
| state change | state card with before→after |
| data/storage | data or storage card |
| event/wait | event/wait card |
| external call | external card |
| error | error card |
| compensation | compensation card |
| boundary/unknown | note or risk card |

Color is secondary. Shape, label, edge condition, ordering, and link must carry meaning in grayscale and print.

## 11.4 Focus card rules

Each first-view card contains:

- numbered action or decision;
- one concise human summary;
- state meaning when necessary;
- a human-labeled link to Atlas evidence; never visible raw `[[wiki/path]]` syntax.

Do not repeat the same non-verified confidence badge on every Focus card. Keep confidence in the machine model and linked note, and show uncertainty in the visible boundary/unknown region. Atlas may display inline confidence where it helps evidence review.

Do not place UUIDs, long symbol paths, raw route names, database columns, or implementation trivia in the first-view label. Those belong in linked notes.

## 11.5 Edge rules

Atlas processing edges state why the story continues. Examples:

```text
verified member
ACTIVE and sale window open
stock reserved
payment authorized
published asynchronously
```

Focus keeps ordinary sequence arrows quiet. Decision cards contain the human rule, and the selected branch may use one short cue such as `통과`, `승인`, or `비동기`. Atlas may show all conditional, error, timeout, retry, cancel, and compensation branches. Focus uses the selected central path and a summarized stop-reason card.

## 11.6 Generate and compose

Focus:

```bash
python scripts/generate_excalidraw_from_visual_model.py \
  architecture/machine/focus-visual-model.json \
  architecture/excalidraw \
  --theme clean
```

Atlas children and master:

```bash
python scripts/generate_excalidraw_from_visual_model.py \
  architecture/machine/atlas-visual-model.json \
  architecture/atlas/excalidraw \
  --theme clean

python scripts/compose_excalidraw_master.py \
  architecture/machine/atlas-visual-model.json \
  architecture/atlas/excalidraw \
  architecture/atlas/excalidraw \
  --link-prefix architecture/atlas/excalidraw
```

Excalidraw frame child elements must be emitted before the frame element.

## 12. Obsidian as a guided graph

Obsidian links support progression; they do not excuse a missing reading path.

Recommended structure:

```text
architecture/
  start-here.md
  visual-index.md
  understanding-map.canvas
  understanding/
  flows/
  unknowns.md
  excalidraw/
  previews/
  atlas/
    index.md
    start-here.md
    visual-index.md
    workspace-stream-map.canvas
    flows/
    actors/
    domains/
    entities/
    states/
    rules/
    codebases/
    excalidraw/
    previews/
  machine/
```

### 12.1 Focus start page

The start page is question-centered:

```text
What are you trying to understand?
→ Read the selected Focus flow
→ Check what remains unknown or out of scope
→ Open Atlas only when needed
```

Generate:

```bash
python scripts/generate_focus_obsidian_docs.py \
  architecture/machine/map-model.json \
  architecture/machine/focus-visual-model.json \
  architecture/machine/understanding-session.json \
  architecture/machine/coverage.json \
  architecture

python scripts/generate_focus_canvas.py \
  architecture/machine/understanding-session.json \
  architecture/understanding-map.canvas \
  --architecture-prefix architecture
```

### 12.2 Atlas notes and Canvas

Generate the detailed graph under `architecture/atlas`:

```bash
python scripts/generate_obsidian_docs.py \
  architecture/machine/map-model.json \
  architecture/machine/atlas-visual-model.json \
  architecture/atlas

python scripts/generate_workspace_canvas.py \
  architecture/machine/map-model.json \
  architecture/machine/atlas-visual-model.json \
  architecture/atlas/workspace-stream-map.canvas \
  --architecture-prefix architecture/atlas
```

## 13. Validation gates

### 13.1 Machine and traceability

```bash
python scripts/validate_map_model.py architecture/machine/map-model.json
python scripts/validate_understanding_session.py architecture/machine/understanding-session.json --map-model architecture/machine/map-model.json
python scripts/validate_coverage.py architecture/machine/coverage.json --session architecture/machine/understanding-session.json
python scripts/validate_evidence_ledger.py architecture/machine/evidence-ledger.json
python scripts/validate_visual_model.py architecture/machine/focus-visual-model.json --map-model architecture/machine/map-model.json
python scripts/validate_visual_model.py architecture/machine/atlas-visual-model.json --map-model architecture/machine/map-model.json
```

### 13.2 Human understanding gate

```bash
python scripts/validate_human_understanding.py \
  architecture/machine/focus-visual-model.json \
  --session architecture/machine/understanding-session.json \
  --coverage architecture/machine/coverage.json \
  --map-model architecture/machine/map-model.json
```

This is a structural proxy, not magical mind reading. It checks:

- first-view node limits;
- contiguous step numbering;
- visible start and success;
- no more than four visible decisions;
- summarized failure reasons;
- relevant unknowns on the diagram;
- explicit Atlas progression;
- reader-contract answers;
- progressive-detail links for collapsed steps.

### 13.3 Render and inspect

```bash
python scripts/validate_excalidraw_output.py architecture/excalidraw
python scripts/validate_excalidraw_output.py architecture/atlas/excalidraw
python scripts/render_excalidraw_preview.py architecture/excalidraw architecture/previews --png
python scripts/render_excalidraw_preview.py architecture/atlas/excalidraw architecture/atlas/previews --png
python scripts/validate_obsidian_links.py <vault-root>
```

Inspect at minimum:

- human overview;
- selected Focus flow;
- Atlas master;
- one state/eligibility diagram;
- one failure or compensation-heavy Atlas flow.

Ask:

```text
Can a reader find START HERE immediately?
Can they follow the central story without source code?
Can they state the answer boundary?
Are important unknowns visible?
Is the path to detail obvious?
Does the Atlas preserve the branches that Focus collapsed?
```

## 14. Change and debug workflows

### 14.1 Before change

Focus first records:

```text
what enters
where the decision is made
who or what is affected
what state or data changes
how the change will be observed
how it can be rolled back
what remains unknown
```

Escalate to Atlas when a mandatory trigger is present or the impact crosses a recorded boundary.

### 14.2 After change

Update:

- evidence ledger claims;
- CodeGraph evidence;
- affected shared stream steps;
- conditions and states;
- tests and runtime observations;
- Focus projection when the human explanation changed;
- Atlas child/master when detailed behavior changed;
- coverage completion and unknowns.

Re-render and revalidate both profiles that were affected.

## 15. Migration

### v4 to v5

```bash
python scripts/migrate_v4_to_v5.py \
  old/map-model.json \
  old/visual-model.json \
  architecture/migration-v5
```

The migration preserves the Atlas model and creates explicit Focus/session/coverage scaffolding. It cannot invent the reader’s question, current risk, or relevant unknowns. Re-analysis is mandatory before approval.

### v3 to v5

```bash
python scripts/migrate_v3_to_v5.py \
  legacy/map-model.json \
  architecture/migration-v5
```

Legacy ordered labels remain `UNVERIFIED` until actors, triggers, guards, states, errors, outcomes, and evidence are rebuilt.

## 16. Delivery acceptance

A delivery is complete only when:

- preflight and workspace registry exist;
- shared map and evidence ledger validate;
- understanding session and routing decision validate;
- coverage distinguishes relevant unknown, out-of-scope, and expansion points;
- Focus answers one explicit question and meets its stop condition;
- Focus first-view constraints pass;
- Atlas exists when requested or required by risk;
- Focus links to Atlas evidence rather than creating a separate truth;
- child drawings exist and Atlas master composition links to them;
- SVG/PNG previews were rendered and inspected;
- the scene declares the v5.1 design-system version and Focus does not expose raw wiki paths;
- the package-owned stencil library is valid and regenerated from source;
- Obsidian and Canvas links validate;
- uncertainties and conflicts remain visible;
- no unverified detail is presented as fact.

## 17. Commands

```text
/im-code-map tools-check
/im-code-map snapshot-check
/im-code-map init
/im-code-map orient
/im-code-map trace "<behavior>"
/im-code-map explain "<question>"
/im-code-map before-change "<change>"
/im-code-map debug "<symptom>"
/im-code-map expand "<boundary>"
/im-code-map atlas
/im-code-map validate
/im-code-map after-change
/im-code-map migrate-v4
/im-code-map migrate-v3
```

Compatibility aliases:

```text
visual-summary → orient
explain-flow → trace
compose-master → atlas generation step
```
