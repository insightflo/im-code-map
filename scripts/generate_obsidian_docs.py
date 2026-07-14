#!/usr/bin/env python3
"""Generate a stream-first, densely linked Obsidian architecture wiki."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from im_code_map_common import evidence_text, read_json, slugify


def q(value: Any) -> str:
    s = str(value).replace('"', '\\"')
    return f'"{s}"'


def frontmatter(kind: str, item_id: str, confidence: str, extra: dict[str, Any] | None = None) -> str:
    lines = ["---", f"type: {q(kind)}", f"id: {q(item_id)}", f"confidence: {q(confidence)}"]
    for key, value in (extra or {}).items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {q(v)}" for v in value)
        else:
            lines.append(f"{key}: {q(value)}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def wikilink(path: str, alias: str | None = None) -> str:
    target = path[:-3] if path.endswith(".md") else path
    return f"[[{target}|{alias}]]" if alias else f"[[{target}]]"


def bullets(values: list[str], fallback: str = "- None evidenced.") -> str:
    return "\n".join(f"- {v}" for v in values) if values else fallback


def evidence_section(items: list[Any]) -> str:
    return bullets([f"`{evidence_text(e)}`" for e in items], "- No direct evidence recorded.")


def write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip() + "\n", encoding="utf-8")


def generate(model: dict[str, Any], visual: dict[str, Any], root: Path) -> None:
    actors = {x["id"]: x for x in model.get("actors", [])}
    domains = {x["id"]: x for x in model.get("domains", [])}
    entities = {x["id"]: x for x in model.get("entities", [])}
    machines = {x["id"]: x for x in model.get("state_machines", [])}
    rules = {x["id"]: x for x in model.get("business_rules", [])}
    streams = {x["id"]: x for x in model.get("business_streams", [])}
    codebases = {x["id"]: x for x in model.get("codebases", [])}
    diagrams = {x["id"]: x for x in visual.get("diagrams", [])}

    # Start here prioritizes user-visible work, then state/rules, then domain/code context.
    primary = max(streams.values(), key=lambda s: len(s.get("steps", []))) if streams else None
    stream_links = [wikilink(f"flows/{s['id']}", s["name"]) + f" · `{s['confidence']}`" for s in streams.values()]
    state_links = [wikilink(f"states/{m['id']}", m["name"]) for m in machines.values()]
    domain_links = [wikilink(f"domains/{d['id']}", d["name"]) for d in domains.values()]
    start = frontmatter("architecture-start", model["workspace_id"], model.get("confidence", "UNVERIFIED"), {"schema_version": model.get("schema_version")})
    start += f"# {model['workspace_id']} architecture\n\n"
    start += "> Read the business stream first. Domain ownership explains *where* work lives; it does not explain *what happens*.\n\n"
    if primary:
        primary_link = wikilink("flows/" + primary["id"], primary["name"])
        start += f"## Primary reading path\n\n1. {primary_link}\n2. {wikilink('visual-index', 'Visual index')}\n3. {wikilink('workspace-stream-map.canvas', 'Workspace stream canvas')}\n"
        if primary.get("diagram_paths"):
            diagram_name = Path(primary["diagram_paths"][0]).name
            start += f"4. {wikilink(f'excalidraw/{diagram_name}', 'Primary Excalidraw stream')}\n"
    start += "\n## Business streams\n\n" + bullets(stream_links)
    start += "\n\n## State and eligibility\n\n" + bullets(state_links)
    start += "\n\n## Domain context\n\n" + bullets(domain_links)
    start += "\n\n## Machine-readable sources\n\n- `map-model.json`\n- `visual-model.json`\n"
    write(root, "start-here.md", start)

    # Actors.
    for actor in actors.values():
        content = frontmatter("actor", actor["id"], actor["confidence"], {"actor_type": actor["type"], "roles": actor.get("roles", [])})
        content += f"# {actor['name']}\n\n## Entry points\n\n{bullets([f'`{x}`' for x in actor.get('entry_points',[])])}\n\n"
        content += f"## Permissions\n\n{bullets(actor.get('permissions',[]))}\n\n## Participating streams\n\n"
        participates = [s for s in streams.values() if actor["id"] in s.get("actor_ids", [])]
        content += bullets([wikilink(f"../flows/{s['id']}", s["name"]) for s in participates])
        content += f"\n\n## Evidence\n\n{evidence_section(actor.get('evidence',[]))}"
        write(root, f"actors/{actor['id']}.md", content)

    # Domain notes are backlinks into streams and ownership, not isolated essays.
    for domain in domains.values():
        content = frontmatter("domain", domain["id"], domain["confidence"], {"domain_type": domain["type"], "streams": domain.get("participating_streams", [])})
        content += f"# {domain['name']}\n\n{domain['purpose']}\n\n"
        content += f"## Responsibilities\n\n{bullets(domain.get('responsibilities',[]))}\n\n"
        content += "## Business streams using this domain\n\n" + bullets([
            wikilink(f"../flows/{sid}", streams[sid]["name"]) for sid in domain.get("participating_streams", []) if sid in streams
        ]) + "\n\n"
        content += "## Owned entities and state\n\n" + bullets([
            wikilink(f"../entities/{eid}", entities[eid]["name"]) for eid in domain.get("owned_entities", []) if eid in entities
        ] + [wikilink(f"../states/{mid}", machines[mid]["name"]) for mid in domain.get("owned_state_machines", []) if mid in machines]) + "\n\n"
        interactions = [i for i in model.get("domain_interactions", []) if i.get("from_domain") == domain["id"] or i.get("to_domain") == domain["id"]]
        content += "## Contracts\n\n"
        if interactions:
            content += "| Direction | Kind | Contract | Streams |\n|---|---|---|---|\n"
            for i in interactions:
                other = i["to_domain"] if i["from_domain"] == domain["id"] else i["from_domain"]
                arrow = "→" if i["from_domain"] == domain["id"] else "←"
                stream_ref = ", ".join(wikilink(f"../flows/{s}", s) for s in i.get("used_by_streams", []))
                content += f"| {arrow} {wikilink(f'../domains/{other}', domains.get(other, {'name':other})['name'])} | `{i['kind']}` / `{i['direction']}` | `{i['contract']}` | {stream_ref} |\n"
        else:
            content += "- No typed cross-domain contract recorded.\n"
        content += "\n## Implementation locations\n\n"
        impl = []
        for cb, paths in domain.get("implementations_by_codebase", {}).items():
            cb_link = wikilink(f"../codebases/{cb}", codebases.get(cb, {"name": cb})["name"])
            impl.append(f"{cb_link}: " + ", ".join(f"`{p}`" for p in paths))
        content += bullets(impl)
        content += f"\n\n## Visuals\n\n- {wikilink('../visual-index', 'Visual index')}\n"
        if domain.get("overview_diagram"):
            content += f"- {wikilink('../excalidraw/' + Path(domain['overview_diagram']).name, 'Domain overview')}\n"
        content += f"\n## Evidence\n\n{evidence_section(domain.get('evidence',[]))}"
        write(root, f"domains/{domain['id']}.md", content)

    # Entity notes.
    for entity in entities.values():
        content = frontmatter("entity", entity["id"], entity["confidence"], {"domain": entity["domain_id"], "states": entity.get("lifecycle_states", [])})
        domain_name = domains.get(entity["domain_id"], {"name": entity["domain_id"]})["name"]
        content += f"# {entity['name']}\n\n- Owner: {wikilink('../domains/' + entity['domain_id'], domain_name)}\n"
        if entity.get("state_machine_id"):
            machine_name = machines.get(entity["state_machine_id"], {"name": entity["state_machine_id"]})["name"]
            content += f"- State machine: {wikilink('../states/' + entity['state_machine_id'], machine_name)}\n"
        content += f"\n## Lifecycle states\n\n{bullets([f'`{s}`' for s in entity.get('lifecycle_states',[])])}\n\n"
        content += "## Eligibility rules\n\n" + bullets([wikilink(f"../rules/{r}", rules[r]["name"]) for r in entity.get("eligibility_rules", []) if r in rules])
        related = []
        for stream in streams.values():
            if any(entity["id"] == c.get("entity_id") for step in stream.get("steps", []) for c in step.get("state_changes", [])) or entity["domain_id"] in stream.get("domain_ids", []):
                related.append(wikilink(f"../flows/{stream['id']}", stream["name"]))
        content += f"\n\n## Related streams\n\n{bullets(related)}\n\n## Evidence\n\n{evidence_section(entity.get('evidence',[]))}"
        write(root, f"entities/{entity['id']}.md", content)

    # State machines.
    for machine in machines.values():
        entity = entities.get(machine["entity_id"], {"name": machine["entity_id"]})
        content = frontmatter("state-machine", machine["id"], machine["confidence"], {"entity": machine["entity_id"], "initial_state": machine["initial_state"]})
        entity_name = entity["name"]
        content += f"# {machine['name']}\n\n- Entity: {wikilink('../entities/' + machine['entity_id'], entity_name)}\n- Initial state: `{machine['initial_state']}`\n"
        content += "\n## States\n\n| State | Terminal | Meaning |\n|---|---:|---|\n"
        for state in machine.get("states", []):
            content += f"| `{state['id']}` | {'yes' if state['terminal'] else 'no'} | {state.get('meaning','')} |\n"
        content += "\n## Transitions\n\n| From | To | Trigger | Guard | Effect | Stream steps |\n|---|---|---|---|---|---|\n"
        for t in machine.get("transitions", []):
            refs = ", ".join(f"`{r}`" for r in t.get("stream_step_refs", []))
            content += f"| `{t['from']}` | `{t['to']}` | {t['trigger']} | {t['guard']} | {t['effect']} | {refs} |\n"
        if machine.get("diagram_path"):
            diagram_name = Path(machine["diagram_path"]).name
            content += f"\n## Diagram\n\n![[../excalidraw/{diagram_name}]]\n"
        content += f"\n## Evidence\n\n{evidence_section(machine.get('evidence',[]))}"
        write(root, f"states/{machine['id']}.md", content)

    # Rules.
    for rule in rules.values():
        content = frontmatter("business-rule", rule["id"], rule["confidence"], {"scope": rule["scope"], "streams": rule.get("used_by_streams", [])})
        content += f"# {rule['name']}\n\n- **Scope:** {rule['scope']}\n- **Condition:** `{rule['condition']}`\n- **Outcome:** {rule['outcome']}\n\n"
        content += "## Used by streams\n\n" + bullets([wikilink(f"../flows/{s}", streams[s]["name"]) for s in rule.get("used_by_streams", []) if s in streams])
        related_entities = [e for e in entities.values() if rule["id"] in e.get("eligibility_rules", [])]
        content += "\n\n## Governs entities\n\n" + bullets([wikilink(f"../entities/{e['id']}", e["name"]) for e in related_entities])
        content += f"\n\n## Evidence\n\n{evidence_section(rule.get('evidence',[]))}"
        write(root, f"rules/{rule['id']}.md", content)

    # Codebases.
    for cb in codebases.values():
        content = frontmatter("codebase", cb["id"], cb["confidence"], {"kind": cb["kind"], "languages": cb.get("languages", [])})
        content += f"# {cb['name']}\n\n- Root: `{cb['root_path']}`\n- Kind: `{cb['kind']}`\n\n## Entry points\n\n{bullets([f'`{p}`' for p in cb.get('entry_points',[])])}\n\n"
        content += "## Implemented domains\n\n" + bullets([wikilink(f"../domains/{d['id']}", d["name"]) for d in domains.values() if cb["id"] in d.get("implementations_by_codebase", {})])
        content += f"\n\n## Evidence\n\n{evidence_section(cb.get('evidence',[]))}"
        write(root, f"codebases/{cb['id']}.md", content)

    # Flows, the primary human-facing artifacts.
    for stream in streams.values():
        content = frontmatter("business-stream", stream["id"], stream["confidence"], {"actors": stream.get("actor_ids", []), "domains": stream.get("domain_ids", [])})
        content += f"# {stream['name']}\n\n{stream['purpose']}\n\n"
        content += f"## Trigger\n\n- Kind: `{stream['trigger']['kind']}`\n- Source: `{stream['trigger']['source']}`\n- Event: **{stream['trigger']['event']}**\n- Entry point: `{stream['trigger']['entry_point']}`\n\n"
        content += "## Actors and systems\n\n" + bullets([wikilink(f"../actors/{a}", actors.get(a, {"name":a})["name"]) for a in stream.get("actor_ids", [])])
        content += "\n\n## Preconditions\n\n"
        if stream.get("preconditions"):
            for pre in stream["preconditions"]:
                rule_links = ", ".join(wikilink(f"../rules/{r}", rules.get(r, {"name":r})["name"]) for r in pre.get("rule_refs", [])) or "none"
                content += f"- **{pre['description']}** Rules: {rule_links}. Failure: `{pre['failure_outcome']}`.\n"
        else:
            content += "- No explicit preconditions beyond request validity.\n"
        content += "\n## Stream\n\n| # | Actor/System | Domain | Kind | Processing | Reads / writes | State change | Rules | Confidence |\n|---:|---|---|---|---|---|---|---|---|\n"
        for step in sorted(stream.get("steps", []), key=lambda s: (s.get("sequence",0), s["id"])):
            actor = actors.get(step["actor_id"], {"name":step["actor_id"]})["name"]
            domain = domains.get(step["domain_id"], {"name":step["domain_id"]})["name"]
            rw = "; ".join((["R: " + ", ".join(f"`{x}`" for x in step.get("reads", []))] if step.get("reads") else []) + (["W: " + ", ".join(f"`{x}`" for x in step.get("writes", []))] if step.get("writes") else []))
            changes = "; ".join(f"`{c['entity_id']} {c['from']}→{c['to']}`" for c in step.get("state_changes", []))
            rule_links = ", ".join(wikilink(f"../rules/{r}", rules.get(r,{"name":r})["name"]) for r in step.get("rule_refs", []))
            actor_link = wikilink("../actors/" + step["actor_id"], actor)
            domain_link = wikilink("../domains/" + step["domain_id"], domain)
            content += f"| {step['sequence']} | {actor_link} | {domain_link} | `{step['kind']}` | <a id=\"{slugify(step['id'].split('.')[-1])}\"></a>**{step['name']}**: {step['action']} | {rw} | {changes} | {rule_links} | `{step['confidence']}` |\n"
        content += "\n## Branches and transitions\n\n| From | Condition / reason | To | Type |\n|---|---|---|---|\n"
        step_names = {s["id"]: s["name"] for s in stream.get("steps", [])}
        for t in sorted(stream.get("transitions", []), key=lambda t: (t.get("priority",0),t["id"])):
            content += f"| `{t['from']}` {step_names.get(t['from'],'')} | **{t['label']}** · {t['condition']} | `{t['to']}` {step_names.get(t['to'],'')} | `{t['kind']}` |\n"
        content += "\n## Terminal outcomes\n\n| Outcome | Type | Terminal step | Observable result |\n|---|---|---|---|\n"
        for outcome in stream.get("outcomes", []):
            content += f"| **{outcome['description']}** | `{outcome['type']}` | `{outcome['terminal_step_id']}` | {outcome['observable_result']} |\n"
        content += "\n## Errors, retries, and compensation\n\n"
        if stream.get("error_paths"):
            for ep in stream["error_paths"]:
                content += f"- `{ep['error']}` at `{ep['from_step_id']}` → handler `{ep['handler_step_id']}` → outcome `{ep['terminal_outcome_id']}`. Retry: {ep['retry_policy']}\n"
        else:
            content += "- No explicit error path modeled. Verify this is intentional.\n"
        for comp in stream.get("compensations", []):
            content += f"- **Compensation `{comp['id']}`:** when {comp['trigger']}, {comp['action']}; restores {comp['restores']}.\n"
        content += "\n## State changes\n\n" + bullets([f"`{x}`" for x in stream.get("state_changes", [])])
        content += "\n\n## Domains touched\n\n" + bullets([wikilink(f"../domains/{d}", domains.get(d,{"name":d})["name"]) for d in stream.get("domain_ids", [])])
        content += "\n\n## Visuals\n\n"
        for path in stream.get("diagram_paths", []):
            name = Path(path).name
            content += f"- {wikilink(f'../excalidraw/{name}', name)}\n"
        if stream.get("diagram_paths"):
            content += f"\n![[../excalidraw/{Path(stream['diagram_paths'][0]).name}]]\n"
        content += f"\n## Evidence\n\n{evidence_section(stream.get('evidence',[]))}"
        write(root, f"flows/{stream['id']}.md", content)

    # Visual index links both child and master diagrams and says what each one is for.
    content = frontmatter("visual-index", model["workspace_id"], model.get("confidence", "UNVERIFIED"))
    content += "# Visual index\n\n"
    content += "## Master map\n\n"
    for comp in visual.get("compositions", []):
        if comp.get("mode") == "merge-elements":
            content += f"- {wikilink('excalidraw/' + Path(comp['output_path']).name, comp['title'])}: composed snapshot of child diagrams.\n"
    content += "\n## Business streams\n\n"
    for d in visual.get("diagrams", []):
        if d["type"] == "business-stream":
            content += f"- {wikilink('excalidraw/' + d['id'] + '.excalidraw', d['title'])}: {d['purpose']}\n"
    content += "\n## State, rules, and context\n\n"
    for d in visual.get("diagrams", []):
        if d["type"] != "business-stream":
            content += f"- {wikilink('excalidraw/' + d['id'] + '.excalidraw', d['title'])}: {d['purpose']}\n"
    content += "\n## Navigation\n\n- " + wikilink("start-here", "Architecture start") + "\n- " + wikilink("workspace-stream-map.canvas", "Workspace stream canvas")
    write(root, "visual-index.md", content)

    # Compact indices create additional graph hubs.
    write(root, "indexes/streams.md", frontmatter("index", "streams", model.get("confidence","UNVERIFIED")) + "# Business streams\n\n" + bullets(stream_links))
    write(root, "indexes/domains.md", frontmatter("index", "domains", model.get("confidence","UNVERIFIED")) + "# Domains\n\n" + bullets(domain_links))
    write(root, "indexes/states-rules.md", frontmatter("index", "states-rules", model.get("confidence","UNVERIFIED")) + "# States and rules\n\n" + bullets(state_links + [wikilink(f"../rules/{r['id']}", r["name"]) for r in rules.values()]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_model", type=Path)
    parser.add_argument("visual_model", type=Path)
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    generate(read_json(args.map_model), read_json(args.visual_model), args.output_root)
    print(f"WROTE linked Obsidian wiki under {args.output_root}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
