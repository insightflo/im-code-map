# Install Plan

Generated at: {{generated_at}}

## Why this exists

`im-code-map` could not start normal architecture analysis because a required tool is missing or not initialized.

Normal mode requires:

```text
git
codegraph
```

OpenWiki is optional in v5.1.0. The default documentation provider is the current AI agent using `agent-native-docs`.

## Missing required tools

{{missing_required_tools}}

## Environment notes

- OS: {{os}}
- Shell: {{shell}}
- Node detected: {{node_detected}}
- npm detected: {{npm_detected}}
- npx detected: {{npx_detected}}

## Suggested install commands

Commands must be selected after checking the current environment and official installation guidance.

```bash
# Example only. Verify before running.
npm install -g @colbymchenry/codegraph
```

## Optional OpenWiki CLI

Use this only if the user explicitly wants OpenWiki CLI and has configured a provider/API key.

```bash
# Optional only.
npm install -g openwiki
openwiki code --init
```

## After installation

Run:

```bash
/im-code-map tools-check
/im-code-map init
```

## Status

BLOCKED_MISSING_CODEGRAPH / READY_AGENT_NATIVE_DOCS
