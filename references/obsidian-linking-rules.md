# Obsidian linking rules

## Goal

Use Obsidian as a guided graph, not a pile of individually respectable but collectively bewildering documents.

## Focus entry path

```text
start-here.md
→ understanding/<session>.md
→ flows/<stream>-focus.md
→ unknowns.md
→ atlas/index.md
```

The start page is question-centered. It must not assume the reader already understands the directory taxonomy.

## Atlas graph

```text
atlas/flows/       complete narratives
atlas/actors/      initiators and participants
atlas/domains/     ownership and contracts
atlas/entities/    business data and lifecycle concepts
atlas/states/      state machines and legal transitions
atlas/rules/       authorization, eligibility, limits, invariants
atlas/codebases/   implementation roots and evidence navigation
atlas/indexes/     alternate entry points
```

## Required links

Focus:

- start → current session, Focus flow, unknowns, Atlas;
- Focus flow → Focus drawing, unknowns, corresponding Atlas flow;
- unknown → next check and relevant Atlas boundary;
- human overview → all first-reading documents.

Atlas:

- flow → actors, domains, entities, states, rules, codebases, child diagram;
- actor → streams;
- domain → streams and typed contracts;
- entity → owner, state machine, rules, and streams;
- state → transition steps and state drawing;
- rule → decision nodes and streams;
- codebase → domains and entry points;
- drawing → note and child/master navigation.

## Canvas roles

Focus Canvas guides:

```text
question → Focus → unknowns → Atlas
```

Atlas Canvas groups:

```text
business streams
state, eligibility, and rules
domain ownership and contracts
codebases and evidence
```

Use file nodes when a real note exists. Label edges with meaning, not “related”.

## Validation

Run `validate_obsidian_links.py` against the vault root. Missing Markdown and Canvas file targets are errors. Excalidraw links are warnings by default and errors in strict release validation.
