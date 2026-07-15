#!/usr/bin/env python3
"""Bounded semantic projection used by im-code-map v5.3.

This module intentionally owns no visual coordinates or colors. It converts a
rich map/visual model into a small, deterministic overview contract that can be
rendered by Excalidraw, SVG, PNG, or another fixed renderer.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

VALID_NODE_KINDS = {
    "entry", "schedule", "actor", "process", "decision", "service",
    "store", "external", "outcome", "risk",
}
VALID_EDGE_KINDS = {"normal", "conditional", "async", "data", "error", "recovery"}
VALID_EMBED_KINDS = {"model", "tool", "rule", "state", "evidence", "technology"}
FOLD_RAW_KINDS = {
    "model": "model", "llm": "model", "tool": "tool", "function": "tool",
    "rule": "rule", "policy": "rule", "guard-rule": "rule",
    "state": "state", "status": "state", "evidence": "evidence", "test": "evidence",
    "technology": "technology", "framework": "technology", "library": "technology",
}


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("input JSON root must be an object")
    return data


def dump_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_slug(value: str, fallback: str = "codebase") -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (normalized or fallback)[:64]


def stable_id(*parts: object, prefix: str = "n") -> str:
    raw = "|".join(str(p) for p in parts if p is not None)
    stem = stable_slug(raw, prefix)[:42]
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    return f"{stem}-{digest}"[:64]


def compact_text(value: Any, limit: int, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    text = re.sub(r"\s+", " ", str(value)).strip()
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "…"


def first_text(obj: dict[str, Any], keys: Iterable[str], limit: int = 999) -> str | None:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return compact_text(value, limit)
        if isinstance(value, (int, float)):
            return compact_text(value, limit)
    return None


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def has_korean(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text))


def infer_node_kind(raw_kind: str, label: str, obj: dict[str, Any]) -> tuple[str, str | None]:
    raw = raw_kind.lower().replace("_", "-").strip()
    combined = f"{raw} {label}".lower()
    if raw in FOLD_RAW_KINDS:
        return "service", FOLD_RAW_KINDS[raw]
    if any(x in combined for x in ("start", "trigger", "entry", "request", "webhook", "route", "input", "시작", "요청", "진입")):
        return "entry", None
    if any(x in combined for x in ("cron", "schedule", "timer", "periodic", "routine", "스케줄", "예약", "주기")):
        return "schedule", None
    if any(x in combined for x in ("actor", "user", "member", "operator", "agent", "reviewer", "owner", "사용자", "회원", "운영자", "에이전트")):
        return "actor", None
    if any(x in combined for x in ("decision", "condition", "guard", "validate", "check", "eligible", "allowed", "가능", "판단", "검사", "확인")):
        return "decision", None
    if any(x in combined for x in ("database", "postgres", "mysql", "redis", "cache", "store", "repository", "table", "persist", "save", "read", "write", "저장", "조회", "데이터")):
        return "store", None
    if any(x in combined for x in ("error", "failure", "failed", "risk", "reject", "deny", "blocked", "timeout", "compens", "recover", "오류", "실패", "거절", "복구", "보상", "차단")):
        return "risk", None
    if any(x in combined for x in ("outcome", "result", "complete", "success", "finish", "return", "end", "완료", "성공", "결과", "종료")):
        return "outcome", None
    if any(x in combined for x in ("external", "third-party", "http", "https", "mcp", "provider", "gateway", "외부", "원격")):
        return "external", None
    if any(x in combined for x in ("service", "worker", "adapter", "queue", "broker", "api", "서비스", "워커", "어댑터", "큐")):
        return "service", None
    if raw in VALID_NODE_KINDS:
        return raw, None
    if obj.get("before") is not None or obj.get("after") is not None or obj.get("stateBefore") is not None:
        return "process", "state"
    return "process", None


def infer_edge_kind(raw_kind: str, label: str) -> str:
    combined = f"{raw_kind} {label}".lower().replace("_", "-")
    if any(x in combined for x in ("recover", "retry", "compens", "resume", "복구", "재시도", "보상", "재개")):
        return "recovery"
    if any(x in combined for x in ("error", "fail", "deny", "reject", "timeout", "blocked", "오류", "실패", "거절", "차단")):
        return "error"
    if any(x in combined for x in ("async", "event", "queue", "publish", "비동기", "이벤트")):
        return "async"
    if any(x in combined for x in ("read", "write", "query", "persist", "data", "저장", "조회")):
        return "data"
    if any(x in combined for x in ("condition", "yes", "no", "true", "false", "if", "when", "통과", "예", "아니오")):
        return "conditional"
    return "normal"


def normalize_embed(value: Any, kind_hint: str | None = None) -> dict[str, str] | None:
    if isinstance(value, str):
        label = compact_text(value, 24)
        if not label:
            return None
        return {"label": label, "kind": kind_hint or "technology"}
    if not isinstance(value, dict):
        return None
    label = first_text(value, ("label", "name", "title", "id", "key"), 24)
    if not label:
        return None
    raw_kind = first_text(value, ("kind", "type", "category"), 30) or kind_hint or "technology"
    kind = FOLD_RAW_KINDS.get(raw_kind.lower().replace("_", "-"), raw_kind.lower())
    if kind not in VALID_EMBED_KINDS:
        kind = kind_hint if kind_hint in VALID_EMBED_KINDS else "technology"
    out = {"label": label, "kind": kind}
    domain = first_text(value, ("domain", "iconDomain", "providerDomain"), 120)
    if domain:
        out["domain"] = domain
    return out


def collect_embeds(obj: dict[str, Any], limit: int = 4) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    mapping = {
        "models": "model", "model": "model", "tools": "tool", "tool": "tool",
        "rules": "rule", "ruleRefs": "rule", "states": "state", "stateRefs": "state",
        "evidence": "evidence", "evidenceRefs": "evidence", "tests": "evidence",
        "technologies": "technology", "technology": "technology", "libraries": "technology",
        "embeds": None, "badges": None,
    }
    seen: set[tuple[str, str]] = set()
    for key, hint in mapping.items():
        for item in as_list(obj.get(key)):
            embed = normalize_embed(item, hint)
            if not embed:
                continue
            signature = (embed["kind"], embed["label"].lower())
            if signature in seen:
                continue
            seen.add(signature)
            result.append(embed)
            if len(result) >= limit:
                return result
    return result


def collect_evidence_refs(obj: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("evidenceRefs", "codeRefs", "sources", "sourceRefs", "files", "filePaths", "tests"):
        for item in as_list(obj.get(key)):
            if isinstance(item, str):
                text = compact_text(item, 240)
            elif isinstance(item, dict):
                text = first_text(item, ("ref", "path", "file", "url", "id", "label"), 240) or ""
            else:
                text = ""
            if text and text not in refs:
                refs.append(text)
            if len(refs) >= 8:
                return refs
    return refs


def normalize_node(raw: Any, index: int, context: str = "node") -> dict[str, Any]:
    obj = raw if isinstance(raw, dict) else {"label": str(raw)}
    raw_id = first_text(obj, ("id", "key", "nodeId", "stepId", "slug"), 64)
    label = first_text(
        obj,
        ("humanLabel", "label", "name", "title", "action", "summary", "description", "id"),
        28,
    ) or f"Step {index + 1}"
    raw_kind = first_text(obj, ("kind", "type", "nodeType", "category", "role"), 40) or "process"
    kind, fold_kind = infer_node_kind(raw_kind, label, obj)
    sub = first_text(
        obj,
        ("sub", "subtitle", "shortDescription", "summary", "description", "stateChange", "contract"),
        44,
    )
    if sub == label:
        sub = None
    detail = first_text(obj, ("detail", "description", "explanation", "notes", "codeSymbol"), 240)
    group = first_text(obj, ("groupId", "group", "phase", "lane", "stage", "domain"), 64)
    importance_raw = obj.get("importance", obj.get("priority", 3))
    try:
        importance = int(importance_raw)
    except Exception:
        importance = 3
    importance = max(1, min(5, importance))
    if kind in {"entry", "outcome"}:
        importance = max(importance, 5)
    elif kind in {"decision", "risk"}:
        importance = max(importance, 4)
    node = {
        "id": raw_id or stable_id(context, index, label),
        "label": compact_text(label, 28),
        "kind": kind,
        "groupId": group or "",
        "importance": importance,
        "embeds": collect_embeds(obj),
        "evidenceRefs": collect_evidence_refs(obj),
        "_foldKind": fold_kind,
        "_index": index,
    }
    if sub:
        node["sub"] = compact_text(sub, 44)
    if detail:
        node["detail"] = compact_text(detail, 240)
    link = first_text(obj, ("link", "note", "obsidianLink", "drawingLink"), 240)
    if link:
        node["link"] = link
    return node


def normalize_edge(raw: Any, index: int, context: str = "edge") -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    source = first_text(raw, ("from", "source", "sourceId", "start", "producer", "origin"), 64)
    target = first_text(raw, ("to", "target", "targetId", "end", "consumer", "destination"), 64)
    if not source or not target:
        return None
    label = first_text(raw, ("label", "condition", "name", "contract", "event"), 24)
    raw_kind = first_text(raw, ("kind", "type", "edgeType", "style"), 40) or "normal"
    kind = infer_edge_kind(raw_kind, label or "")
    edge = {
        "id": first_text(raw, ("id", "key"), 64) or stable_id(context, index, source, target, label, prefix="e"),
        "from": source,
        "to": target,
        "kind": kind,
        "evidenceRefs": collect_evidence_refs(raw),
        "_index": index,
    }
    if label:
        edge["label"] = compact_text(label, 24)
    condition = first_text(raw, ("condition", "guard", "when"), 80)
    if condition and condition != label:
        edge["condition"] = condition
    return edge


def choose_items(items: list[dict[str, Any]], question: str, item_id: str | None, count: int) -> list[dict[str, Any]]:
    if not items:
        return []
    if item_id:
        exact = [x for x in items if str(x.get("id", "")) == item_id or str(x.get("name", "")) == item_id]
        if exact:
            return exact[:count]
    tokens = {t for t in re.findall(r"[a-zA-Z0-9가-힣]{2,}", question.lower())}
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for i, item in enumerate(items):
        hay = " ".join(str(item.get(k, "")) for k in ("id", "name", "title", "summary", "description")).lower()
        score = sum(1 for token in tokens if token in hay)
        scored.append((score, -i, item))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    if scored[0][0] == 0:
        return items[:count]
    return [row[2] for row in scored[:count]]


def list_from_first(obj: dict[str, Any], keys: Iterable[str]) -> list[Any]:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, list) and value:
            return value
    return []


def extract_graph(source: dict[str, Any], question: str, profile: str, stream_id: str | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    # Already bounded overview map.
    if source.get("version") == "1.0" and isinstance(source.get("nodes"), list):
        nodes = [normalize_node(n, i, "overview") for i, n in enumerate(source.get("nodes", []))]
        edges = [e for i, raw in enumerate(source.get("edges", [])) if (e := normalize_edge(raw, i, "overview-edge"))]
        return nodes, edges, {"selected": "existing-overview"}

    containers: list[dict[str, Any]] = []
    diagrams = source.get("diagrams")
    if isinstance(diagrams, list) and diagrams:
        containers = choose_items([x for x in diagrams if isinstance(x, dict)], question, stream_id, 2 if profile == "orientation" else 1)
    else:
        streams = source.get("streams") or source.get("businessStreams") or source.get("flows")
        if isinstance(streams, list) and streams:
            containers = choose_items([x for x in streams if isinstance(x, dict)], question, stream_id, 3 if profile == "orientation" else 1)
    if not containers:
        containers = [source]

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    for c_index, container in enumerate(containers):
        context = first_text(container, ("id", "name", "title"), 64) or f"flow-{c_index+1}"
        raw_nodes = list_from_first(container, ("nodes", "steps", "activities", "stages", "flow", "actions"))
        raw_edges = list_from_first(container, ("edges", "transitions", "links", "connections"))

        local_nodes: list[dict[str, Any]] = []
        for i, raw in enumerate(raw_nodes):
            node = normalize_node(raw, i, context)
            original = node["id"]
            if original in used_ids:
                node["id"] = stable_id(context, original, i)
            used_ids.add(node["id"])
            if not node["groupId"]:
                node["groupId"] = stable_slug(context, f"flow-{c_index+1}")
            local_nodes.append(node)
        local_id_map: dict[str, str] = {}
        for raw, node in zip(raw_nodes, local_nodes):
            if isinstance(raw, dict):
                rid = first_text(raw, ("id", "key", "nodeId", "stepId", "slug"), 64)
                if rid:
                    local_id_map[rid] = node["id"]
        nodes.extend(local_nodes)

        for i, raw in enumerate(raw_edges):
            edge = normalize_edge(raw, i, context)
            if not edge:
                continue
            edge["from"] = local_id_map.get(edge["from"], edge["from"])
            edge["to"] = local_id_map.get(edge["to"], edge["to"])
            edges.append(edge)

        # Support next/dependsOn references embedded in steps.
        for i, raw in enumerate(raw_nodes):
            if not isinstance(raw, dict) or i >= len(local_nodes):
                continue
            src = local_nodes[i]["id"]
            for key in ("next", "nextId", "to", "targets"):
                for target in as_list(raw.get(key)):
                    target_id = target if isinstance(target, str) else first_text(target, ("id", "key", "target"), 64) if isinstance(target, dict) else None
                    if target_id and target_id in local_id_map:
                        edges.append({
                            "id": stable_id(context, src, target_id, key, prefix="e"),
                            "from": src,
                            "to": local_id_map[target_id],
                            "kind": "normal",
                            "evidenceRefs": [],
                            "_index": len(edges),
                        })
            for dep in as_list(raw.get("dependencies") or raw.get("dependsOn")):
                dep_id = dep if isinstance(dep, str) else first_text(dep, ("id", "key", "source"), 64) if isinstance(dep, dict) else None
                if dep_id and dep_id in local_id_map:
                    edges.append({
                        "id": stable_id(context, dep_id, src, "dependency", prefix="e"),
                        "from": local_id_map[dep_id],
                        "to": src,
                        "kind": "normal",
                        "label": "dependency",
                        "evidenceRefs": [],
                        "_index": len(edges),
                    })

        # If there are no explicit edges, preserve the narrative sequence.
        if len(local_nodes) > 1 and not any(e["from"] in {n["id"] for n in local_nodes} for e in edges):
            for left, right in zip(local_nodes, local_nodes[1:]):
                edges.append({
                    "id": stable_id(context, left["id"], right["id"], prefix="e"),
                    "from": left["id"], "to": right["id"], "kind": "normal",
                    "evidenceRefs": [], "_index": len(edges),
                })

    return nodes, edges, {"selected": [first_text(c, ("id", "name", "title"), 64) for c in containers]}


def dedupe_graph(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    node_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if node["id"] not in node_by_id:
            node_by_id[node["id"]] = node
    edge_seen: set[tuple[str, str, str, str]] = set()
    clean_edges: list[dict[str, Any]] = []
    for edge in edges:
        if edge["from"] not in node_by_id or edge["to"] not in node_by_id or edge["from"] == edge["to"]:
            continue
        key = (edge["from"], edge["to"], edge.get("label", ""), edge.get("kind", "normal"))
        if key in edge_seen:
            continue
        edge_seen.add(key)
        clean_edges.append(edge)
    return list(node_by_id.values()), clean_edges


def fold_leaf_nodes(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], max_embeds: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        incoming[edge["to"]].append(edge)
        outgoing[edge["from"]].append(edge)
    node_by_id = {n["id"]: n for n in nodes}
    remove: set[str] = set()
    for node in nodes:
        fold_kind = node.get("_foldKind")
        if fold_kind not in VALID_EMBED_KINDS:
            continue
        ins = incoming.get(node["id"], [])
        outs = outgoing.get(node["id"], [])
        if len(ins) != 1 or outs:
            continue
        owner = node_by_id.get(ins[0]["from"])
        if not owner or len(owner.get("embeds", [])) >= max_embeds:
            continue
        embed = {"label": compact_text(node["label"], 24), "kind": fold_kind}
        signature = (embed["kind"], embed["label"].lower())
        existing = {(x["kind"], x["label"].lower()) for x in owner.get("embeds", [])}
        if signature not in existing:
            owner.setdefault("embeds", []).append(embed)
        remove.add(node["id"])
    if not remove:
        return nodes, edges
    return [n for n in nodes if n["id"] not in remove], [e for e in edges if e["from"] not in remove and e["to"] not in remove]


def shortest_path(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[str]:
    ids = {n["id"] for n in nodes}
    incoming_count = {nid: 0 for nid in ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if e["from"] in ids and e["to"] in ids and e.get("kind") not in {"error", "recovery"}:
            outgoing[e["from"]].append(e["to"])
            incoming_count[e["to"]] += 1
    entries = [n["id"] for n in nodes if n["kind"] == "entry"] or [nid for nid, count in incoming_count.items() if count == 0]
    outcomes = {n["id"] for n in nodes if n["kind"] == "outcome"}
    if not outcomes:
        outcomes = {nid for nid in ids if not outgoing.get(nid)}
    for start in entries:
        queue = deque([start])
        prev: dict[str, str | None] = {start: None}
        while queue:
            cur = queue.popleft()
            if cur in outcomes and cur != start:
                path: list[str] = []
                while cur is not None:
                    path.append(cur)
                    cur = prev[cur]  # type: ignore[assignment]
                return list(reversed(path))
            for nxt in outgoing.get(cur, []):
                if nxt not in prev:
                    prev[nxt] = cur
                    queue.append(nxt)
    return [n["id"] for n in sorted(nodes, key=lambda x: x.get("_index", 0))]


def select_bounded(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], max_nodes: int, max_edges: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    path = shortest_path(nodes, edges)
    degree: dict[str, int] = defaultdict(int)
    for e in edges:
        degree[e["from"]] += 1
        degree[e["to"]] += 1
    path_set = set(path)
    mandatory: list[str] = []
    for nid in path:
        if nid not in mandatory:
            mandatory.append(nid)
    for n in nodes:
        if n["kind"] in {"entry", "outcome"} and n["id"] not in mandatory:
            mandatory.append(n["id"])
    # Keep risk nodes attached to the main path: they explain where the story stops.
    for e in edges:
        if e.get("kind") in {"error", "recovery"} and (e["from"] in path_set or e["to"] in path_set):
            candidate = e["to"] if e["from"] in path_set else e["from"]
            if candidate not in mandatory:
                mandatory.append(candidate)
    if len(mandatory) > max_nodes:
        keep = [mandatory[0]]
        special = [nid for nid in mandatory[1:-1] if next((n for n in nodes if n["id"] == nid and n["kind"] in {"decision", "external", "store", "risk"}), None)]
        for nid in special:
            if len(keep) < max_nodes - 1:
                keep.append(nid)
        remaining = [nid for nid in mandatory[1:-1] if nid not in keep]
        slots = max_nodes - len(keep) - 1
        if slots > 0 and remaining:
            for i in range(slots):
                keep.append(remaining[min(len(remaining) - 1, round(i * (len(remaining) - 1) / max(1, slots - 1)))])
        keep.append(mandatory[-1])
        mandatory = list(dict.fromkeys(keep))[:max_nodes]
    scores: list[tuple[int, int, str]] = []
    for n in nodes:
        score = n.get("importance", 3) * 20 + min(degree[n["id"]], 8)
        if n["id"] in path_set:
            score += 100
        if n["kind"] in {"decision", "external", "store", "risk"}:
            score += 12
        scores.append((score, -int(n.get("_index", 0)), n["id"]))
    scores.sort(reverse=True)
    selected_ids = list(mandatory)
    for _, _, nid in scores:
        if len(selected_ids) >= max_nodes:
            break
        if nid not in selected_ids:
            selected_ids.append(nid)
    selected_set = set(selected_ids)
    selected_nodes = [n for n in nodes if n["id"] in selected_set]
    selected_nodes.sort(key=lambda n: (selected_ids.index(n["id"]) if n["id"] in selected_ids else 9999, n.get("_index", 0)))
    selected_edges = [e for e in edges if e["from"] in selected_set and e["to"] in selected_set]
    # Prefer focus-path and semantically meaningful edges under the cap.
    path_pairs = {(a, b) for a, b in zip(path, path[1:])}
    selected_edges.sort(key=lambda e: (
        0 if (e["from"], e["to"]) in path_pairs else 1,
        0 if e.get("kind") in {"error", "recovery", "conditional"} else 1,
        e.get("_index", 0),
    ))
    selected_edges = selected_edges[:max_edges]
    path = [nid for nid in path if nid in selected_set]
    return selected_nodes, selected_edges, path


def assign_groups(nodes: list[dict[str, Any]], max_groups: int, question: str) -> list[dict[str, Any]]:
    korean = has_korean(question)
    # Preserve first-seen semantic groups, but collapse excess groups into phases.
    raw_groups: list[str] = []
    for n in nodes:
        raw = compact_text(n.get("groupId", ""), 64)
        if raw and raw not in raw_groups:
            raw_groups.append(raw)
    if not raw_groups or len(raw_groups) > max_groups:
        labels_ko = ["시작·입력", "준비·대기", "핵심 처리", "결과·복구"]
        labels_en = ["Intake", "Preparation", "Core flow", "Outcome"]
        labels = labels_ko if korean else labels_en
        group_count = min(max_groups, 4, max(1, (len(nodes) + 4) // 5))
        labels = labels[:group_count]
        for i, n in enumerate(nodes):
            bucket = min(group_count - 1, int(i * group_count / max(1, len(nodes))))
            n["groupId"] = stable_slug(labels[bucket], f"group-{bucket+1}")
        return [
            {"id": stable_slug(label, f"group-{i+1}"), "label": compact_text(label, 24), "order": i}
            for i, label in enumerate(labels)
        ]

    groups: list[dict[str, Any]] = []
    id_map: dict[str, str] = {}
    for i, raw in enumerate(raw_groups):
        gid = stable_slug(raw, f"group-{i+1}")
        if gid in id_map.values():
            gid = f"{gid}-{i+1}"
        id_map[raw] = gid
        label = re.sub(r"[-_]+", " ", raw).strip() or f"Group {i+1}"
        groups.append({"id": gid, "label": compact_text(label, 24), "order": i})
    for n in nodes:
        n["groupId"] = id_map.get(n.get("groupId", ""), groups[0]["id"])
    return groups


def clean_public_fields(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    for n in nodes:
        n.pop("_foldKind", None)
        n.pop("_index", None)
        n["embeds"] = n.get("embeds", [])[:4]
        if not n.get("evidenceRefs"):
            n.pop("evidenceRefs", None)
        if not n.get("sub"):
            n.pop("sub", None)
        if not n.get("detail"):
            n.pop("detail", None)
    for e in edges:
        e.pop("_index", None)
        if not e.get("evidenceRefs"):
            e.pop("evidenceRefs", None)
        if not e.get("label"):
            e.pop("label", None)
        if not e.get("condition"):
            e.pop("condition", None)


def extract_unknowns(source: dict[str, Any]) -> tuple[list[str], list[str]]:
    unknowns: list[str] = []
    expansions: list[str] = []
    coverage = source.get("coverage") if isinstance(source.get("coverage"), dict) else source
    for key in ("unknown_relevant", "unknownRelevant", "unknowns"):
        for item in as_list(coverage.get(key)):
            text = compact_text(item.get("summary") if isinstance(item, dict) else item, 160)
            if text and text not in unknowns:
                unknowns.append(text)
    for key in ("expansion_points", "expansionPoints", "nextQuestions"):
        for item in as_list(coverage.get(key)):
            text = compact_text(item.get("summary") if isinstance(item, dict) else item, 160)
            if text and text not in expansions:
                expansions.append(text)
    return unknowns[:5], expansions[:8]


def build_overview_map(
    source: dict[str, Any],
    *,
    project_name: str,
    question: str,
    profile: str = "orientation",
    stream_id: str | None = None,
    max_nodes: int = 20,
    max_edges: int = 36,
    max_groups: int = 4,
    max_embeds: int = 4,
    project_slug: str | None = None,
    source_ref: str | None = None,
) -> dict[str, Any]:
    max_nodes = max(1, min(24, int(max_nodes)))
    max_edges = max(0, min(48, int(max_edges)))
    max_groups = max(1, min(6, int(max_groups)))
    max_embeds = max(0, min(4, int(max_embeds)))
    nodes, edges, extraction_meta = extract_graph(source, question, profile, stream_id)
    nodes, edges = dedupe_graph(nodes, edges)
    nodes, edges = fold_leaf_nodes(nodes, edges, max_embeds)
    nodes, edges = dedupe_graph(nodes, edges)
    nodes, edges, focus_path = select_bounded(nodes, edges, max_nodes, max_edges)
    groups = assign_groups(nodes, max_groups, question)
    unknowns, expansions = extract_unknowns(source)
    clean_public_fields(nodes, edges)
    result: dict[str, Any] = {
        "version": "1.0",
        "project": {
            "name": compact_text(project_name, 64),
            "slug": project_slug or stable_slug(project_name),
        },
        "question": compact_text(question, 180),
        "profile": profile if profile in {"orientation", "focus", "domain", "change", "debug"} else "orientation",
        "limits": {
            "maxNodes": max_nodes,
            "maxEdges": max_edges,
            "maxGroups": max_groups,
            "maxEmbedsPerNode": max_embeds,
        },
        "groups": groups,
        "nodes": nodes,
        "edges": edges,
        "focusPath": focus_path,
        "unknowns": unknowns,
        "expansionPoints": expansions,
        "sourceSummary": compact_text(f"Projection selected {extraction_meta.get('selected')} from the detailed source; omitted detail remains in Atlas and evidence notes.", 500),
    }
    if source_ref:
        result["project"]["sourceRef"] = compact_text(source_ref, 160)
    canonical = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    result["mapHash"] = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result


def validate_overview_map(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    nodes = data.get("nodes") if isinstance(data.get("nodes"), list) else []
    edges = data.get("edges") if isinstance(data.get("edges"), list) else []
    groups = data.get("groups") if isinstance(data.get("groups"), list) else []
    limits = data.get("limits") if isinstance(data.get("limits"), dict) else {}
    max_nodes = min(24, int(limits.get("maxNodes", 24)))
    max_edges = min(48, int(limits.get("maxEdges", 48)))
    max_groups = min(6, int(limits.get("maxGroups", 6)))
    max_embeds = min(4, int(limits.get("maxEmbedsPerNode", 4)))
    if data.get("version") != "1.0":
        errors.append("version must be 1.0")
    if not nodes:
        errors.append("nodes must contain at least one node")
    if len(nodes) > max_nodes or len(nodes) > 24:
        errors.append(f"node cap exceeded: {len(nodes)} > {min(max_nodes, 24)}")
    if len(edges) > max_edges or len(edges) > 48:
        errors.append(f"edge cap exceeded: {len(edges)} > {min(max_edges, 48)}")
    if len(groups) > max_groups or len(groups) > 6:
        errors.append(f"group cap exceeded: {len(groups)} > {min(max_groups, 6)}")
    ids: list[str] = []
    group_ids = {g.get("id") for g in groups if isinstance(g, dict)}
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            errors.append(f"nodes[{i}] must be an object")
            continue
        nid = n.get("id")
        if not isinstance(nid, str) or not nid:
            errors.append(f"nodes[{i}].id is required")
            continue
        ids.append(nid)
        label = n.get("label")
        if not isinstance(label, str) or not label:
            errors.append(f"node {nid}: label is required")
        elif len(label) > 28:
            errors.append(f"node {nid}: label exceeds 28 characters")
        if n.get("kind") not in VALID_NODE_KINDS:
            errors.append(f"node {nid}: invalid kind {n.get('kind')!r}")
        if n.get("groupId") not in group_ids:
            errors.append(f"node {nid}: unknown groupId {n.get('groupId')!r}")
        if len(n.get("sub", "")) > 44:
            errors.append(f"node {nid}: sub exceeds 44 characters")
        embeds = n.get("embeds", [])
        if not isinstance(embeds, list) or len(embeds) > max_embeds:
            errors.append(f"node {nid}: embeds exceed cap {max_embeds}")
        for embed in embeds if isinstance(embeds, list) else []:
            if not isinstance(embed, dict) or embed.get("kind") not in VALID_EMBED_KINDS:
                errors.append(f"node {nid}: invalid embed")
        if re.search(r"(?:^|\s)(?:[A-Za-z]:\\|/[^ ]+|\w+\.(?:ts|tsx|js|py|java|go|rs))(?:$|\s)", f"{label} {n.get('sub','')}"):
            warnings.append(f"node {nid}: raw path/symbol should move to detail or evidenceRefs")
    if len(ids) != len(set(ids)):
        errors.append("node ids must be unique")
    id_set = set(ids)
    edge_ids: list[str] = []
    incident: dict[str, int] = defaultdict(int)
    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            errors.append(f"edges[{i}] must be an object")
            continue
        eid = e.get("id")
        if not isinstance(eid, str) or not eid:
            errors.append(f"edges[{i}].id is required")
        else:
            edge_ids.append(eid)
        if e.get("from") not in id_set or e.get("to") not in id_set:
            errors.append(f"edge {eid}: endpoints must reference existing nodes")
        else:
            incident[e["from"]] += 1
            incident[e["to"]] += 1
        if e.get("kind") not in VALID_EDGE_KINDS:
            errors.append(f"edge {eid}: invalid kind {e.get('kind')!r}")
        if len(e.get("label", "")) > 24:
            errors.append(f"edge {eid}: label exceeds 24 characters")
    if len(edge_ids) != len(set(edge_ids)):
        errors.append("edge ids must be unique")
    if not any(n.get("kind") == "entry" for n in nodes if isinstance(n, dict)):
        warnings.append("overview has no explicit entry node")
    if not any(n.get("kind") == "outcome" for n in nodes if isinstance(n, dict)):
        warnings.append("overview has no explicit outcome node")
    isolated = [nid for nid in ids if incident.get(nid, 0) == 0 and len(ids) > 1]
    if isolated:
        warnings.append("isolated nodes: " + ", ".join(isolated))
    focus = data.get("focusPath", [])
    if not isinstance(focus, list) or any(x not in id_set for x in focus):
        errors.append("focusPath must reference existing nodes")
    elif len(focus) < 2 and len(nodes) > 1:
        warnings.append("focusPath is too short to communicate a start-to-outcome story")
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {"nodes": len(nodes), "edges": len(edges), "groups": len(groups), "focusPath": len(focus) if isinstance(focus, list) else 0},
    }
