# Focus vs Deep Atlas

## Focus

Use when the reader has one concrete question. Completion means the question and its evidence boundary can be explained, not that the whole codebase has been catalogued.

Required:

- question and stop condition;
- selected actor/trigger and flow;
- 6–12 numbered first-view steps, wrapped into no more than four cards per semantic phase row;
- visible success result;
- summarized stop reasons;
- relevant unknowns;
- obvious Atlas link;
- traceability to the shared stream model.

## Deep Atlas

Use for full branch/state/rule/impact reasoning, risky changes, cross-repository work, takeover, audit, incident analysis, or explicit full-map requests.

Required:

- complete modeled branches and terminal outcomes;
- state machines and business rules;
- failure, timeout, retry, cancel, and compensation;
- domain contracts and code evidence;
- child drawings and composed master;
- detailed Obsidian graph.

## Invariant

Focus and Atlas must not disagree. When they do, record `CONFLICT` and resolve the evidence before presenting either view as verified.
