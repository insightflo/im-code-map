# Legacy → v4 migration report

Source: `/mnt/data/review_output/701. Papercompany/architecture/map-model.json`

- Domains migrated: **22**
- Legacy path summaries migrated as incomplete streams: **4**
- Actors, triggers, guards, state machines, business rules, errors, retries, and compensation were **not present** in the legacy model and were not invented.
- Output confidence is `UNVERIFIED`; this file is a re-analysis checklist, not an approved architecture map.

## Required remediation

1. Identify concrete entry points and actors for every critical stream.
2. Extract authorization, eligibility, and policy guards.
3. Reconstruct entity state machines and step-level state changes.
4. Add error, retry, timeout, cancellation, and compensation paths.
5. Generate child stream/state diagrams, compose a master map, render previews, and run visual QA.
6. Connect flow, domain, entity, state, rule, codebase, and evidence notes in Obsidian.
