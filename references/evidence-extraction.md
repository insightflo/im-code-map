# Evidence extraction rules

## Purpose

Convert repository evidence into a business-stream model without inventing missing semantics.

## Evidence priority

Use the strongest available source for each claim:

1. executable source and declarative configuration used at runtime;
2. tests that assert behavior or state transitions;
3. schemas, migrations, API contracts, event contracts, and policy definitions;
4. observed runtime traces or logs with reproducible context;
5. maintained repository documentation;
6. comments and names only as discovery hints, never as sole proof of a material rule.

## Start from observable triggers

Search for concrete initiators:

- HTTP/GraphQL/RPC routes
- UI actions and command handlers
- queue/event subscribers
- scheduled jobs and workers
- CLI commands
- webhook handlers
- agent/tool invocations
- database or lifecycle hooks

For each trigger capture the exact entry point, actor/system identity, payload or command shape, and authorization boundary.

## Trace until observable termination

For every path, continue through:

```text
trigger → entry point → policy/validation → reads → decisions → writes/state changes
→ external/async boundary → success, rejection, failure, timeout, retry, cancel, or compensation
```

A call graph ending at a service method is not necessarily a business-flow ending. Stop only at an observable result or an explicitly unresolved runtime boundary.

## Extract decisions as predicates

A decision requires:

- the predicate or policy function;
- pass and fail branches;
- data used by the predicate;
- user/system-visible consequence;
- evidence locator.

Do not translate `canOrder()` into a guessed formula. Inspect the implementation and tests. If the implementation cannot be found, retain `canOrder()` as an unresolved policy boundary with `UNVERIFIED` or `PARTIAL` confidence.

## Extract state transitions

When a write changes lifecycle behavior, record:

- entity;
- state before;
- state after;
- trigger;
- guard;
- side effects;
- stream step;
- rollback/compensation behavior.

Do not collapse `PENDING → RESERVED → PAID` into “order updated.”

## External and asynchronous boundaries

For external calls capture:

- request contract;
- response/result handling;
- timeout behavior;
- retry policy;
- idempotency mechanism;
- compensation or reconciliation;
- unresolved provider behavior.

For events capture publication timing, transactional relationship, consumer(s), delivery guarantee when evidenced, and whether the initiating response waits for consumption.

## Confidence assignment

- `VERIFIED`: direct source/test/schema/config/runtime proof.
- `PARTIAL`: path is mostly proven but one material boundary remains unresolved.
- `DOC_ONLY`: repository documentation is the only evidence.
- `UNVERIFIED`: migrated label or plausible relationship without proof.
- `CONFLICT`: reliable sources disagree; preserve both claims and identify the conflict.

## Minimum evidence record

```json
{
  "source": "path/to/file",
  "locator": "symbol, route, line range, test, schema key, or command",
  "excerpt": "short non-sensitive summary or bounded excerpt",
  "tool": "codegraph|source-inspection|test|runtime|docs",
  "captured_at": "ISO-8601"
}
```
