# Immutable remote repository snapshot mode

Use `remote-connector-snapshot` when source can be read through a repository connector but a local checkout or CodeGraph is unavailable.

## What makes it normal mode

A remote analysis is normal mode only when all of the following are true:

1. Resolve a full 40-character commit SHA before reading evidence.
2. Fetch every evidence file at that exact SHA.
3. Record the repository path and file blob SHA.
4. Record exact line ranges and a short, faithful excerpt.
5. Cross-check important behavior across different evidence classes when available, especially route, service, test, schema, configuration, and runtime evidence.
6. Keep every claim inside the fetched evidence boundary.
7. Record unresolved callers, dynamic dispatch, generated code, runtime-only behavior, and omitted packages in `coverage.json`.
8. Validate `repository-snapshot.json` before generating diagrams.

The connector's repository search index is discovery only. Search snippets can identify candidate files but cannot support a final claim until the file is fetched at the pinned commit.

## Confidence rules

- `VERIFIED`: source behavior is supported by fetched immutable code plus a corroborating test, schema, route, configuration, or runtime record.
- `PARTIAL`: the fetched code supports the local behavior but a material upstream/downstream edge remains unfetched or dynamic.
- `DOC_ONLY`: only prose or comments support the claim.
- `UNVERIFIED`: the file or branch was not fetched at the pinned SHA.
- `CONFLICT`: immutable sources disagree.

A blob SHA proves file identity, not behavioral correctness. A test proves only what it actually asserts. Humans remain distressingly necessary.

## Hybrid mode

When both connector and local checkout are available:

- compare the local `git rev-parse HEAD` with `snapshot.commit_sha`;
- compare relevant file blob hashes where possible;
- run CodeGraph at the same commit;
- mark any mismatch `CONFLICT` and do not merge evidence silently.

## Minimum output

```text
architecture/machine/repository-snapshot.json
architecture/machine/tool-preflight-report.md
architecture/machine/evidence-ledger.json
architecture/machine/coverage.json
```
