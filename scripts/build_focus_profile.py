#!/usr/bin/env python3
"""Build the human-first Focus visual projection from the shared v5 evidence model.

Focus is not a lossy replacement for the Atlas. It is a question-scoped projection:
selected happy-path steps remain visible, omitted implementation detail is traceable,
failure branches are summarized, and unknown/out-of-scope boundaries stay explicit.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from im_code_map_common import read_json, write_json

KIND_MAP = {
    "start": "start", "process": "process", "action": "process", "decision": "decision",
    "event": "event", "wait": "wait", "data-read": "data", "data-write": "storage",
    "state-change": "state-change", "external-call": "external", "error-handler": "error",
    "compensation": "compensation", "end": "end",
}


def find_path(stream: dict[str, Any], target: str) -> tuple[list[str], list[dict[str, Any]]]:
    """Find a deterministic path from stream start to target terminal step."""
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in stream.get("transitions", []):
        outgoing[t["from"]].append(t)
    for items in outgoing.values():
        items.sort(key=lambda x: (int(x.get("priority", 999999)), x.get("id", "")))
    start = stream["start_step_id"]
    queue = deque([start])
    previous: dict[str, tuple[str, dict[str, Any]]] = {}
    seen = {start}
    while queue:
        current = queue.popleft()
        if current == target:
            break
        for transition in outgoing.get(current, []):
            nxt = transition["to"]
            if nxt not in seen:
                seen.add(nxt)
                previous[nxt] = (current, transition)
                queue.append(nxt)
    if target not in seen:
        raise RuntimeError(f"no path from {start} to success target {target}")
    nodes = [target]
    edges: list[dict[str, Any]] = []
    cur = target
    while cur != start:
        prev, edge = previous[cur]
        nodes.append(prev)
        edges.append(edge)
        cur = prev
    nodes.reverse(); edges.reverse()
    return nodes, edges


def choose_visible_steps(path_steps: list[dict[str, Any]], max_nodes: int) -> list[dict[str, Any]]:
    """Choose the story skeleton without collapsing a critical pre-execution gate.

    The previous implementation filled optional process slots strictly in source order.
    In long flows with several decisions, that could preserve an early context-normalization
    step while silently collapsing the rule-heavy process immediately before an external
    call.  The rendered Focus diagram then appeared to jump straight from checkout to an
    adapter, hiding workspace/trust/secret preflight.

    Mandatory semantic nodes remain fixed. Optional nodes are ranked by reader value:
    processes directly guarding an external call, rule-bearing steps, state/data writes,
    events, and then remaining context. Source order is restored after selection.
    """
    mandatory = {"start", "end", "decision", "state-change", "external-call"}
    selected = [step for step in path_steps if step.get("kind") in mandatory]
    selected_ids = {step["id"] for step in selected}

    def score(index: int, step: dict[str, Any]) -> tuple[int, int]:
        next_kind = path_steps[index + 1].get("kind") if index + 1 < len(path_steps) else None
        value = 0
        if next_kind == "external-call":
            value += 1000  # preserve the last safety/preflight gate before side effects
        value += min(4, len(step.get("rule_refs") or [])) * 180
        value += min(3, len(step.get("state_changes") or [])) * 150
        value += min(4, len(step.get("writes") or [])) * 70
        value += min(4, len(step.get("reads") or [])) * 35
        if step.get("kind") == "event":
            value += 120
        elif step.get("kind") == "process":
            value += 80
        return value, -index

    candidates = [
        (index, step)
        for index, step in enumerate(path_steps)
        if step["id"] not in selected_ids
    ]
    candidates.sort(key=lambda item: score(item[0], item[1]), reverse=True)
    for _, step in candidates:
        if len(selected) >= max_nodes:
            break
        selected.append(step)
        selected_ids.add(step["id"])

    # Very small paths may still have room after ranked candidates; keep the fallback
    # deterministic and preserve the original story order in the final projection.
    for step in path_steps:
        if len(selected) >= max_nodes:
            break
        if step["id"] not in selected_ids:
            selected.append(step)
            selected_ids.add(step["id"])
    selected.sort(key=lambda step: path_steps.index(step))
    return selected


def override_for(session: dict[str, Any], step: dict[str, Any]) -> tuple[str, str]:
    presentation = session.get("presentation", {})
    entry = presentation.get("step_labels", {}).get(step["id"], {})
    label = entry.get("label") or step.get("name") or step["id"]
    summary = entry.get("summary") or step.get("action") or ""
    return label, summary


def confidence_min(values: list[str]) -> str:
    rank = {"VERIFIED": 4, "PARTIAL": 3, "DOC_ONLY": 2, "UNVERIFIED": 1, "CONFLICT": 0}
    if not values:
        return "UNVERIFIED"
    return min(values, key=lambda x: rank.get(x, -1))


def cap_summary_words(text: str, max_words: int = 32) -> str:
    """Keep first-view card prose inside the visual-model word budget.

    Traceability is preserved in source_refs, reader_contract, and the linked Atlas note;
    this only prevents a generated summary card from invalidating the Focus model.
    Newlines are retained where possible so bullet cards remain scannable.
    """
    if max_words < 2:
        return "…" if text.strip() else ""
    tokens = text.split()
    if len(tokens) <= max_words:
        return text

    remaining = max_words - 1
    output_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        words = line.split()
        if remaining <= 0:
            break
        take = min(len(words), remaining)
        output_lines.append(" ".join(words[:take]))
        remaining -= take
        if take < len(words):
            break
    if not output_lines:
        return "…"
    output_lines[-1] = output_lines[-1].rstrip(".,;:!?…") + "…"
    return "\n".join(output_lines)


def assign_phase_lanes(nodes: list[dict[str, Any]], language: str, columns: int = 4) -> list[dict[str, Any]]:
    """Wrap a Focus story into compact, numbered, left-to-right phase rows.

    Every row preserves the same reading direction. The renderer routes the transition
    through whitespace between phase panels rather than forcing a visual snake.
    """
    lanes: list[dict[str, Any]] = []
    for row_start in range(0, len(nodes), columns):
        row_index = row_start // columns
        row_nodes = nodes[row_start:row_start + columns]
        lane_id = f"focus-phase-{row_index + 1}"
        first = row_nodes[0]["label"].split(". ", 1)[-1]
        last = row_nodes[-1]["label"].split(". ", 1)[-1]
        if language == "ko":
            label = f"{row_index + 1}단계 · {first}" if first == last else f"{row_index + 1}단계 · {first} → {last}"
        else:
            label = f"Phase {row_index + 1} · {first}" if first == last else f"Phase {row_index + 1} · {first} → {last}"
        lanes.append({
            "id": lane_id, "label": label, "order": row_index, "kind": "phase",
            "icon": "process", "source_ref": row_nodes[0].get("stream_step_ref", ""),
        })
        for offset, node in enumerate(row_nodes):
            node["lane"] = lane_id
            node["order"] = offset
    return lanes


def build_focus(map_model: dict[str, Any], session: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    stream_id = session.get("selected_stream_id")
    streams = {s["id"]: s for s in map_model.get("business_streams", [])}
    if not stream_id or stream_id not in streams:
        raise RuntimeError("Focus trace requires selected_stream_id that exists in map-model")
    stream = streams[stream_id]
    success = next((o for o in stream.get("outcomes", []) if o.get("type") == "success"), None)
    if not success:
        raise RuntimeError(f"stream {stream_id} has no success outcome")
    path_ids, path_edges = find_path(stream, success["terminal_step_id"])
    step_by_id = {s["id"]: s for s in stream.get("steps", [])}
    path_steps = [step_by_id[x] for x in path_ids]
    max_nodes = 12
    visible = choose_visible_steps(path_steps, max_nodes)
    visible_ids = {s["id"] for s in visible}
    language = session.get("language", "en")
    p = session.get("presentation", {})

    flow_nodes: list[dict[str, Any]] = []
    collapsed_since_last: list[str] = []
    for idx, step in enumerate(path_steps):
        if step["id"] not in visible_ids:
            collapsed_since_last.append(step["id"])
            continue
        label, summary = override_for(session, step)
        node_id = "focus-" + step["id"].replace(".", "-")
        node = {
            "id": node_id, "label": f"{len(flow_nodes)+1}. {label}",
            "kind": KIND_MAP.get(step.get("kind"), "process"),
            "frame": "focus-main", "lane": "focus-story", "order": len(flow_nodes),
            "summary": cap_summary_words(summary), "icon": "auto", "source_refs": [step["id"]],
            "confidence": step.get("confidence", "UNVERIFIED"),
            "stream_step_ref": step["id"], "details_link": f"[[atlas/flows/{stream_id}]]",
            "role": "decision" if step.get("kind") == "decision" else "primary-story",
            "step_number": len(flow_nodes)+1,
        }
        if collapsed_since_last:
            node["collapsed_refs"] = list(collapsed_since_last)
            collapsed_since_last.clear()
        changes = step.get("state_changes", [])
        if changes:
            node["state_before"] = ", ".join(str(x.get("from")) for x in changes)
            node["state_after"] = ", ".join(str(x.get("to")) for x in changes)
        flow_nodes.append(node)
    if collapsed_since_last and flow_nodes:
        flow_nodes[-1].setdefault("collapsed_refs", []).extend(collapsed_since_last)

    phase_lanes = assign_phase_lanes(flow_nodes, language, columns=4)

    # Join visible story nodes. Conditions are inherited from the underlying path segment.
    path_index = {sid: i for i, sid in enumerate(path_ids)}
    edge_by_pair = {(e["from"], e["to"]): e for e in path_edges}
    flow_edges: list[dict[str, Any]] = []
    for seq, (left, right) in enumerate(zip(visible, visible[1:]), start=1):
        li, ri = path_index[left["id"]], path_index[right["id"]]
        segment = path_ids[li:ri+1]
        seg_edges = [edge_by_pair[(a, b)] for a, b in zip(segment, segment[1:])]
        decisive = next((e for e in seg_edges if e.get("kind") in {"conditional", "error", "timeout"}), seg_edges[-1])
        # The decision card already explains the rule. On the first-view canvas, only the
        # chosen branch gets a tiny cue; ordinary transitions stay visually silent.
        is_decision_branch = left.get("kind") == "decision"
        label = ("통과" if language == "ko" else "proceed") if is_decision_branch else ("비동기" if decisive.get("kind") == "async-event" and language == "ko" else "async" if decisive.get("kind") == "async-event" else "")
        condition = ""
        # The selected success route remains visually primary even when the source edge is conditional.
        flow_edges.append({
            "id": f"focus-edge-{seq}",
            "from": "focus-" + left["id"].replace(".", "-"),
            "to": "focus-" + right["id"].replace(".", "-"),
            "kind": "happy-path" if decisive.get("kind") != "async-event" else "async-event",
            "label": label, "condition": condition, "sequence": seq,
            "source_refs": [e["id"] for e in seg_edges],
            "confidence": confidence_min([e.get("confidence", "UNVERIFIED") for e in seg_edges]),
            **({"style": "dashed"} if decisive.get("kind") == "async-event" else {})
        })

    failure_labels = p.get("stop_reason_labels") or [o.get("description", o["id"]) for o in stream.get("outcomes", []) if o.get("type") != "success"]
    relevant_unknowns = coverage.get("unknown_relevant", [])
    expansion_points = coverage.get("expansion_points", [])
    failure_node = {
        "id": "focus-stop-reasons", "label": "왜 흐름이 멈추는가" if language == "ko" else "Why the flow stops",
        "kind": "risk", "frame": "focus-context", "lane": "focus-context-lane", "order": 0,
        "summary": cap_summary_words("\n".join(f"• {x}" for x in failure_labels[:6])), "icon": "auto",
        "source_refs": [o["id"] for o in stream.get("outcomes", []) if o.get("type") != "success"],
        "confidence": stream.get("confidence", "UNVERIFIED"), "details_link": f"[[atlas/flows/{stream_id}#errors-timeouts-and-retries]]",
        "role": "failure-summary", "collapsed_refs": [x.get("id", "") for x in stream.get("error_paths", [])]
    }
    unknown_text = "\n".join(f"• {x['label']}" for x in relevant_unknowns[:4]) or ("• 현재 목적을 막는 미확인 사항 없음" if language == "ko" else "• No unresolved item blocks the current purpose")
    unknown_node = {
        "id": "focus-required-unknowns", "label": "아직 확인되지 않은 것" if language == "ko" else "Still unknown",
        "kind": "note", "frame": "focus-context", "lane": "focus-context-lane", "order": 1,
        "summary": cap_summary_words(unknown_text), "icon": "auto", "source_refs": [x["id"] for x in relevant_unknowns],
        "confidence": confidence_min([x.get("confidence", "UNVERIFIED") for x in relevant_unknowns]) if relevant_unknowns else "VERIFIED",
        "details_link": "[[unknowns]]", "role": "unknown"
    }
    expansion_text = "\n".join(f"• {x['label']}" for x in expansion_points[:4]) or ("• 필요 시 주변 흐름을 확장" if language == "ko" else "• Expand adjacent flows when needed")
    atlas_node = {
        "id": "focus-open-atlas", "label": p.get("atlas_label") or ("전체 지도 열기" if language == "ko" else "Open Deep Atlas"),
        "kind": "note", "frame": "focus-context", "lane": "focus-context-lane", "order": 2,
        "summary": cap_summary_words(expansion_text), "icon": "auto", "source_refs": [x["id"] for x in expansion_points],
        "confidence": "PARTIAL", "details_link": "[[atlas/index]]", "role": "atlas-link"
    }

    primary_ids = [n["id"] for n in flow_nodes]
    focus_diagram = {
        "id": f"focus-{stream_id}", "profile": "focus",
        "title": p.get("flow_title") or stream.get("name", stream_id), "type": "focus-flow",
        "purpose": session["expected_outcome"], "source_refs": [stream_id, session["session_id"]],
        "format_targets": ["excalidraw", "excalidraw-automate", "svg-preview"],
        "layout": {"direction": "phase-rows", "lane_axis": "phase", "node_width": 295, "node_height": 142, "horizontal_gap": 78, "vertical_gap": 84},
        "frames": [
            {"id": "focus-main", "label": "START HERE · 중심 흐름" if language == "ko" else "START HERE · Primary story", "order": 0, "purpose": "정상 흐름을 왼쪽에서 오른쪽으로 읽는다." if language == "ko" else "Read the expected path left to right.", "source_refs": [stream_id]},
            {"id": "focus-context", "label": "경계와 다음 탐색" if language == "ko" else "Boundaries and next exploration", "order": 1, "purpose": "실패 상세를 펼치지 않고 핵심 이유, 미확인 사항, Atlas 진입점을 보여 준다." if language == "ko" else "Summarize stop reasons, unknowns, and deeper navigation.", "source_refs": [session["session_id"]]}
        ],
        "lanes": phase_lanes + [
            {"id": "focus-context-lane", "label": "처음에는 요약하고 필요할 때 확장" if language == "ko" else "Summarize first, expand when needed", "order": 0, "kind": "context", "icon": "note", "source_ref": session["session_id"]}
        ],
        "nodes": flow_nodes + [failure_node, unknown_node, atlas_node], "edges": flow_edges,
        "navigation": {"parent": "human-overview", "children": [], "related_notes": [f"architecture/understanding/{session['session_id']}.md", f"architecture/flows/{stream_id}-focus.md", "architecture/unknowns.md", "architecture/atlas/index.md"]},
        "reader_contract": {
            "start_here_node_id": primary_ids[0], "primary_story_node_ids": primary_ids,
            "answers": {
                "who_starts": p.get("actor_label") or ", ".join(stream.get("actor_ids", [])[:2]),
                "what_they_want": p.get("intent_label") or stream.get("purpose", ""),
                "key_decisions": ", ".join(n["label"].split(". ",1)[-1] for n in flow_nodes if n.get("role") == "decision"),
                "success_change": p.get("success_label") or success.get("observable_result", "")
            },
            "does_not_answer": session.get("scope", {}).get("out_of_scope", []) or ["Full implementation detail"],
            "stop_reasons": failure_labels,
            "deeper_links": [f"[[atlas/flows/{stream_id}]]", "[[atlas/index]]"] + [f"[[unknowns#{x['id']}]]" for x in relevant_unknowns],
            "required_unknowns": [x["label"] for x in relevant_unknowns]
        },
        "legend": [
            {"kind": "primary-story", "label": "1→N", "meaning": "처음 읽는 중심 흐름" if language == "ko" else "Primary story for the first read"},
            {"kind": "failure-summary", "label": "STOP", "meaning": "실패 분기를 상세 선 대신 요약" if language == "ko" else "Failure branches summarized rather than expanded"},
            {"kind": "atlas-link", "label": "DETAIL", "meaning": "상태·오류·보상·코드 근거를 더 깊이 탐색" if language == "ko" else "Open deeper state, failure, compensation, and evidence detail"}
        ],
        "evidence": stream.get("evidence", []), "confidence": stream.get("confidence", "UNVERIFIED")
    }

    overview_nodes = [
        {"id":"overview-start","label":"START HERE · 시스템 한 줄" if language=="ko" else "START HERE · System in one line","kind":"start","frame":"overview-main","lane":"overview-lane","order":0,
         "summary":cap_summary_words(p.get("system_summary") or map_model.get("workspace_id", "")),"icon":"auto","source_refs":[map_model.get("workspace_id","")],"confidence":map_model.get("confidence","UNVERIFIED"),"details_link":"[[architecture/start-here]]","role":"context","step_number":1},
        {"id":"overview-question","label":"질문에서 시작" if language=="ko" else "Begin with a question","kind":"process","frame":"overview-main","lane":"overview-lane","order":1,
         "summary":cap_summary_words(session["question"]),"icon":"auto","source_refs":[session["session_id"]],"confidence":"VERIFIED","details_link":f"[[understanding/{session['session_id']}]]","role":"primary-story","step_number":2},
        {"id":"overview-flow","label":"한 흐름을 끝까지" if language=="ko" else "Trace one flow end to end","kind":"process","frame":"overview-main","lane":"overview-lane","order":2,
         "summary":f"{len(flow_nodes)}개의 중심 단계 · 실패 이유 {len(failure_labels)}개" if language=="ko" else f"{len(flow_nodes)} primary steps · {len(failure_labels)} stop reasons",
         "icon":"auto","source_refs":[stream_id],"confidence":stream.get("confidence","UNVERIFIED"),"details_link":f"[[flows/{stream_id}-focus]]","role":"primary-story","step_number":3},
        {"id":"overview-boundary","label":"현재 이해의 경계" if language=="ko" else "Current understanding boundary","kind":"risk","frame":"overview-main","lane":"overview-lane","order":3,
         "summary":f"관련 미확인 {len(relevant_unknowns)}개 · 범위 밖 {len(coverage.get('unknown_out_of_scope',[]))}개" if language=="ko" else f"{len(relevant_unknowns)} relevant unknowns · {len(coverage.get('unknown_out_of_scope',[]))} out of scope",
         "icon":"auto","source_refs":[x['id'] for x in relevant_unknowns],"confidence":"PARTIAL","details_link":"[[unknowns]]","role":"unknown","step_number":4},
        {"id":"overview-atlas","label":"Deep Atlas 열기" if language=="ko" else "Open Deep Atlas","kind":"note","frame":"overview-main","lane":"overview-lane","order":4,
         "summary":"상태 전이, 오류, timeout, 보상, 도메인, 코드 근거를 확인한다." if language=="ko" else "Inspect state transitions, failures, timeouts, compensation, domains, and evidence.",
         "icon":"auto","source_refs":["atlas"],"confidence":"PARTIAL","details_link":"[[atlas/index]]","role":"atlas-link","step_number":5}
    ]
    overview_edges=[]
    for i,(a,b) in enumerate(zip(overview_nodes,overview_nodes[1:]),1):
        overview_edges.append({"id":f"overview-edge-{i}","from":a["id"],"to":b["id"],"kind":"happy-path","label":"","condition":"","sequence":i,"source_refs":[session["session_id"]],"confidence":"VERIFIED","style":"solid"})
    overview = {
        "id":"human-overview","profile":"focus","title":p.get("overview_title") or "Human-first codebase understanding","type":"human-overview",
        "purpose":"질문에서 시작해 한 흐름을 이해하고, 모름과 Atlas 확장 지점을 잃지 않는다." if language=="ko" else "Begin with one question, understand one flow, and retain unknown and Atlas expansion boundaries.",
        "source_refs":[session["session_id"],stream_id],"format_targets":["excalidraw","excalidraw-automate","svg-preview"],
        "layout":{"direction":"left-to-right","lane_axis":"none","node_width":285,"node_height":140,"horizontal_gap":78,"vertical_gap":55},
        "frames":[{"id":"overview-main","label":"START HERE · 질문에서 깊이로","order":0,"purpose":"Focus를 먼저 읽고 필요한 경우에만 Atlas로 이동한다.","source_refs":[session["session_id"]]}],
        "lanes":[{"id":"overview-lane","label":"사람이 읽는 순서","order":0,"kind":"context","icon":"note","source_ref":session["session_id"]}],
        "nodes":overview_nodes,"edges":overview_edges,
        "navigation":{"parent":"","children":[f"focus-{stream_id}"],"related_notes":["architecture/start-here.md",f"architecture/understanding/{session['session_id']}.md",f"architecture/flows/{stream_id}-focus.md","architecture/unknowns.md","architecture/atlas/index.md"]},
        "reader_contract":{"start_here_node_id":"overview-start","primary_story_node_ids":[n["id"] for n in overview_nodes],
            "answers":{"who_starts":p.get("actor_label") or "A reader with a concrete question","what_they_want":session["expected_outcome"],"key_decisions":"Focus first; Atlas when risk, change, or unresolved boundaries require it.","success_change":"The reader can explain the selected flow and its current evidence boundary."},
            "does_not_answer":session.get("scope",{}).get("out_of_scope",[]) or ["Every subsystem"],"stop_reasons":[],"deeper_links":[f"[[flows/{stream_id}-focus]]","[[atlas/index]]"],"required_unknowns":[x["label"] for x in relevant_unknowns]},
        "legend":[],"evidence":session.get("evidence",[]),"confidence":stream.get("confidence","UNVERIFIED")
    }

    return {
        "schema_version":"5.0.0","profile":"focus","workspace_id":map_model["workspace_id"],
        "generated_at":session["created_at"],"source_map_model":"architecture/machine/map-model.json",
        "source_understanding_session":"architecture/machine/understanding-session.json",
        "icon_registry":"icons/icon-registry.json",
        "reader_policy":{"intended_reader":session.get("audience","newcomer"),"primary_question":session["question"],"first_view_target_seconds":30,"detail_policy":"progressive-disclosure","implementation_identifiers":"notes-only","max_primary_story_nodes":12,"failure_detail_mode":"summary-card","show_step_numbers":True},
        "style_profile":{"theme":"clean","font_family":2,"max_card_words":32,"max_nodes_per_frame":14,"default_direction":"left-to-right","happy_path_emphasis":True,"failure_detail_mode":"summary-card","show_step_numbers":True},
        "diagrams":[overview,focus_diagram],"compositions":[]
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_model",type=Path); parser.add_argument("understanding_session",type=Path); parser.add_argument("coverage",type=Path); parser.add_argument("output",type=Path)
    args=parser.parse_args()
    model=build_focus(read_json(args.map_model),read_json(args.understanding_session),read_json(args.coverage))
    write_json(args.output,model)
    print(f"WROTE: {args.output} ({len(model['diagrams'])} Focus diagrams)")
    return 0
if __name__=='__main__': raise SystemExit(main())
