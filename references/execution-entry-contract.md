# Execution entry contract

At the beginning of an interactive run, establish two things before expensive analysis.

## Output surface

- Ask whether the user wants an Obsidian vault and Excalidraw drawings.
- Accept the vault/output path when supplied.
- When no path is supplied, create a portable output directory and state where it was written.
- Never silently write into an arbitrary vault.

## Analysis scope

- `guided` (default for an unfamiliar or large repository): quick scan and bounded orientation map first, then deep-dive selected domains or flows.
- `full`: batch-analyze all material domains and build Deep Atlas. Use only when requested, for a small repository, or for audit/takeover work.
- `focus`: answer one concrete flow/change/debug question.

For non-interactive automation, default to `guided`, record the decision in `understanding-session.json`, and leave explicit expansion points instead of pretending the entire codebase was understood.
