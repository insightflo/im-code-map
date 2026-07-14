# Tool Preflight Report

Generated at: {{generated_at}}
Workspace: {{workspace_id}}

## Scope

- Workspace root: {{workspace_root}}
- Obsidian vault: {{obsidian_vault_or_none}}
- Install mode: {{install_mode}}

## Codebase candidates

| Codebase | Path | Included | Kind | Evidence | Confidence |
|---|---|---:|---|---|---|
| {{codebase_id}} | {{root_path}} | {{included}} | {{kind}} | {{evidence}} | {{confidence}} |

## Required tools

| Tool | Check command | Status | Version / Output | Action |
|---|---|---|---|---|
| git | `git --version` | {{status}} | {{output}} | REQUIRED |
| CodeGraph | `command -v codegraph && codegraph version` | {{status}} | {{output}} | REQUIRED: install/init before analysis |

## Supporting tools

| Tool | Check command | Status | Version / Output | Action |
|---|---|---|---|---|
| Node.js | `node --version` | {{status}} | {{output}} | Needed only for npm-based installs |
| npm | `npm --version` | {{status}} | {{output}} | Needed only for npm-based installs |
| npx | `npx --version` | {{status}} | {{output}} | Optional helper |
| Python | `python --version` or `python3 --version` | {{status}} | {{output}} | Optional helper for scripts |
| OpenWiki | `command -v openwiki && openwiki --help` | {{status}} | {{output}} | OPTIONAL: use only when explicitly requested/configured |
| Obsidian Excalidraw Plugin | `<vault>/.obsidian/plugins/obsidian-excalidraw-plugin/manifest.json` | {{status}} | {{output}} | Optional viewer/automation runtime |

## Documentation provider decision

```text
{{documentation_provider}}
```

Allowed values:

```text
DOC_PROVIDER_AGENT_NATIVE
DOC_PROVIDER_OPENWIKI_OPTIONAL
DOC_PROVIDER_MANUAL_DOCS_PARTIAL
```

## Installation plan

```bash
{{install_commands}}
```

## Installation results

| Command | Exit code | Result | Notes |
|---|---:|---|---|
| {{command}} | {{exit_code}} | {{result}} | {{notes}} |

## Initialization results

| Codebase | CodeGraph | Documentation provider | Excalidraw output | Notes |
|---|---|---|---|---|
| {{codebase_id}} | {{codegraph_result}} | {{documentation_provider_result}} | {{excalidraw_result}} | {{notes}} |

## Uncertainties

- {{uncertainty}}

## Gate decision

```text
{{gate_decision}}
```

Allowed next commands:

```text
{{allowed_next_commands}}
```

Blocked commands:

```text
{{blocked_commands}}
```

## Status

READY_AGENT_NATIVE_DOCS / READY_OPENWIKI_OPTIONAL / BLOCKED_PREINIT / BLOCKED_MISSING_CODEGRAPH / BLOCKED_NOT_INITIALIZED / PARTIAL_OBSIDIAN_ONLY / FAILED / NEEDS_MANUAL_REVIEW

## If blocked

When `codegraph` is missing, status must be:

```text
BLOCKED_MISSING_CODEGRAPH
```

Allowed outputs while blocked:

```text
architecture/machine/tool-preflight-report.md
architecture/install-plan.md
```

Repository/domain analysis must not start unless the user explicitly requests `EMERGENCY_MANUAL_PARTIAL` mode.

When `openwiki` is missing, do not block normal mode. Use:

```text
DOC_PROVIDER_AGENT_NATIVE
```
