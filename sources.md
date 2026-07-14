# Sources checked for im-code-map v5.1.0

Checked date: 2026-07-14 Asia/Singapore

These sources guide the skill’s analysis and presentation behavior. They do not prove facts about a target repository. Target-system claims still require source, tests, schemas, configuration, runtime evidence, or approved project documentation.

## Partial codebase understanding as a bounded work strategy

Sean Goedecke, “In defense of not understanding your codebase” (2026-07-11):
https://www.seangoedecke.com/in-defense-of-not-understanding-your-codebase/

Observed guidance used by v5:

- Large codebases cannot always be held as a complete mental model by one person or team.
- An abandoned system can be approached by understanding one flow end-to-end, making careful changes, and expanding from there.
- LLMs may weaken detailed theory-building while also helping construct a useful partial model quickly.

Limits:

- This is an engineering argument and experience report, not a quantitative guarantee of productivity or safety.
- v5 therefore treats partial understanding as conditional and bounded, never as permission to change unverified high-risk behavior.

## Beginner-oriented workflow derived from the same argument

Manual Onboarding, “코드베이스를 완전히 몰라도 안전하게 시작하는 법” (2026-07-13):
https://manual-onboarding.pages.dev/onboarding/concepts/20260714-codebase-understanding/index.html

Observed guidance used by v5:

- Narrow the task to one input-processing-output flow.
- Record unknowns and distinguish whether they affect the current change.
- Define sufficient understanding by the ability to explain impact and rollback, not by memorizing every line.
- High-impact boundaries such as authentication, payment, and personal data require broader review.
- Tool output is a map for verification, not final proof.

Limits:

- The page explicitly states that it is not an empirical guarantee of onboarding duration, defect rate, or productivity.

## Progressive disclosure

Nielsen Norman Group, “Progressive Disclosure”:
https://www.nngroup.com/articles/progressive-disclosure/

Observed guidance used by v5:

- Show the most important material first and disclose advanced detail on request.
- Make the path into deeper detail obvious and label it so the reader knows what will be found.
- Too many disclosure levels can cause people to get lost; v5 therefore exposes two major levels: Focus and Atlas.

Skill consequence:

- Focus is the default first-view projection.
- Atlas is the clearly labeled second level.
- Omitted detail is traceable through links and `collapsed_refs`; it is not silently deleted.

## C4 dynamic diagrams

Official C4 model dynamic-diagram documentation:
https://c4model.com/diagrams/dynamic

Observed guidance used by v5:

- Dynamic diagrams show how elements collaborate at runtime for a particular story, use case, or feature.
- Numbered interactions can communicate ordering in a free-form layout.
- Dynamic diagrams should be used selectively for meaningful or complicated interactions.

Skill consequence:

- Focus diagrams use numbered interactions for one selected behavior.
- Atlas does not generate a runtime diagram for every trivial method call.

## CodeGraph

Official repository: https://github.com/colbymchenry/codegraph
Official documentation: https://colbymchenry.github.io/codegraph/

Behavior relied on by the skill:

- `codegraph init` and `codegraph status` establish graph availability.
- `codegraph explore` supports end-to-end discovery.
- `query`, `callers`, `callees`, and `impact` expose machine-readable JSON options.
- Static analysis may stop at dynamic runtime boundaries; those boundaries must remain explicit.

Skill consequence:

- CodeGraph is required in normal mode as structural evidence.
- It is not proof of a business rule by itself.

## OpenWiki

Official repository: https://github.com/langchain-ai/openwiki

Behavior relied on by the skill:

- Repository mode uses explicit code commands such as `openwiki code --init`.
- Provider/model configuration may be required.

Skill consequence:

- OpenWiki is optional.
- Agent-native documentation is the default.

## Excalidraw raw format and frames

Official developer documentation:
https://docs.excalidraw.com/docs/codebase/json-schema
https://docs.excalidraw.com/docs/codebase/frames

Behavior relied on by the skill:

- A scene contains ordered elements, app state, and files.
- Frame children should appear before their frame element.

Skill consequence:

- Generators preserve frame ordering and validators check it.

## Obsidian Excalidraw and ExcalidrawAutomate

Official repository:
https://github.com/zsviczian/obsidian-excalidraw-plugin

Official API overview:
https://zsviczian.github.io/obsidian-excalidraw-plugin/API/attributes_functions_overview.html

Behavior relied on by the skill:

- Drawings can contain Obsidian links and participate in backlinks/transclusion.
- Atomic child drawings can be combined into larger views.
- ExcalidrawAutomate supports editable native elements and embeddable child composition.

Skill consequence:

- Focus drawings link to notes and Atlas detail.
- Atlas child files remain canonical and the master is composed.
- Raw `.excalidraw` remains mandatory even when optional automation scripts are emitted.

## JSON Canvas

Official specification:
https://jsoncanvas.org/spec/1.0/

Behavior relied on by the skill:

- Canvas contains nodes and edges.
- File and group nodes support a navigable workspace.

Skill consequence:

- Focus Canvas guides question → flow → unknowns → Atlas.
- Atlas Canvas connects streams, states/rules, domains, codebases, and evidence.

## Icon and library policy

Official Excalidraw library repository:
https://github.com/excalidraw/excalidraw-libraries

Skill consequence:

- v5 bundles no third-party icon artwork or fonts.
- `icons/icon-registry.json` uses native vector primitives and ASCII fallbacks.
- External library items require source, license, attribution, exact-item, and redistribution review before bundling.


## Excalidraw Libraries and v5.1 visual references

Official public library directory:
https://libraries.excalidraw.com/

Official Excalidraw initial-data API:
https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api/props/initialdata

Observed guidance used by v5.1:

- Excalidraw supports reusable library items and importable `.excalidrawlib` assets.
- Public libraries listed in the official directory expose their license metadata; this does not automatically license unrelated GitHub collections.
- v5.1 therefore ships its own native-vector stencil library and treats external collections as optional research or user-installed assets.

Visual pattern references reviewed without copying assets:

- `Prakash-sa/system-design-ultimatum`: topic folders, shared components, generated previews. No repository-wide license file was found during review, so assets are not redistributed.
- `swaymun/system-design-excalidraws`: practical system-design study diagrams; its README credits some well-designed components to another creator, so assets are not redistributed.
- `karanpratapsingh/system-design`: concise system-design diagrams and an import workflow.
- `aretecode/system-design-templates-excalidraw`: grouped rough-shape stencil workflow under MIT.
- `Bowen-0x00/obsidian-excalidraw-example-vault`: Obsidian-oriented example vault and scripts.

Skill consequence:

- layout grammar may be studied; exact shapes are copied only after item-level license verification;
- `libraries/im-code-map-architecture.excalidrawlib` is generated entirely from package-owned primitives;
- external library intake follows `references/external-library-policy.md`.
