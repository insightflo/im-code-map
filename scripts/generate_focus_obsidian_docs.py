#!/usr/bin/env python3
"""Generate the v5 human-first Obsidian entry path for one understanding session."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from im_code_map_common import read_json


def q(value: Any) -> str:
    return '"' + str(value).replace('"', '\\"') + '"'


def frontmatter(kind: str, item_id: str, confidence: str = "PARTIAL") -> str:
    return f"---\ntype: {q(kind)}\nid: {q(item_id)}\nconfidence: {q(confidence)}\nprofile: \"focus\"\n---\n\n"


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bullets(values: list[str], fallback: str = "- 없음") -> str:
    return "\n".join(f"- {x}" for x in values) if values else fallback


def generate(map_model: dict[str, Any], focus_visual: dict[str, Any], session: dict[str, Any], coverage: dict[str, Any], root: Path) -> None:
    lang = session.get("language", "en")
    stream_id = session.get("selected_stream_id")
    stream = next((s for s in map_model.get("business_streams", []) if s.get("id") == stream_id), None)
    if stream is None:
        raise RuntimeError(f"selected stream not found: {stream_id}")
    p = session.get("presentation", {})
    flow_title = p.get("flow_title") or stream.get("name", stream_id)
    overview_title = p.get("overview_title") or "Human-first codebase understanding"
    session_id = session["session_id"]
    focus_diagram = next(d for d in focus_visual.get("diagrams", []) if d.get("type") == "focus-flow")
    overview_diagram = next(d for d in focus_visual.get("diagrams", []) if d.get("type") == "human-overview")
    answers = focus_diagram["reader_contract"]["answers"]

    if lang == "ko":
        start = frontmatter("understanding-start", map_model["workspace_id"], map_model.get("confidence", "PARTIAL"))
        start += f"# {overview_title}\n\n"
        start += "> 전체를 먼저 외우지 않습니다. 지금 궁금한 한 흐름을 끝까지 읽고, 필요한 경계만 넓힙니다.\n\n"
        start += "## 지금 답하려는 질문\n\n"
        start += f"**{session['question']}**\n\n{session['expected_outcome']}\n\n"
        start += "## 읽는 순서\n\n"
        start += f"1. [[understanding/{session_id}|현재 이해 세션]]\n"
        start += f"2. [[flows/{stream_id}-focus|{flow_title}]]\n"
        start += "3. [[unknowns|아직 확인되지 않은 것과 범위 밖 영역]]\n"
        start += "4. [[atlas/index|상태·오류·보상·코드 근거가 필요한 경우 Deep Atlas]]\n\n"
        start += "## 그림\n\n"
        start += "![[excalidraw/human-overview.excalidraw]]\n\n"
        start += "## 이 첫 화면에서 알 수 있는 것\n\n"
        start += f"- 시작 주체: {answers['who_starts']}\n- 목적: {answers['what_they_want']}\n- 핵심 판단: {answers['key_decisions']}\n- 성공 시 변화: {answers['success_change']}\n\n"
        start += "## 이 첫 화면이 답하지 않는 것\n\n" + bullets(session.get("scope", {}).get("out_of_scope", []))
    else:
        start = frontmatter("understanding-start", map_model["workspace_id"], map_model.get("confidence", "PARTIAL"))
        start += f"# {overview_title}\n\n> Do not memorize the whole codebase first. Trace one useful flow and expand only when the boundary matters.\n\n"
        start += f"## Current question\n\n**{session['question']}**\n\n{session['expected_outcome']}\n\n"
        start += f"## Reading path\n\n1. [[understanding/{session_id}|Understanding session]]\n2. [[flows/{stream_id}-focus|{flow_title}]]\n3. [[unknowns|Unknown and out-of-scope boundaries]]\n4. [[atlas/index|Deep Atlas]]\n\n![[excalidraw/human-overview.excalidraw]]"
    write(root, "start-here.md", start)

    # Session note
    sdoc = frontmatter("understanding-session", session_id, "PARTIAL")
    sdoc += f"# {session['question']}\n\n"
    if lang == "ko":
        sdoc += f"## 목적\n\n{session['expected_outcome']}\n\n## 완료 기준\n\n{session['stop_condition']}\n\n"
        sdoc += "## 현재 범위\n\n" + bullets(session["scope"]["in_scope"]) + "\n\n## 현재 범위 밖\n\n" + bullets(session["scope"]["out_of_scope"]) + "\n\n"
        sdoc += f"## 선택된 깊이\n\n- 프로필: `{session['routing_decision']['selected_profile']}`\n- 이유: {session['routing_decision']['reason']}\n- 위험 수준: `{session['risk_assessment']['level']}`\n- Atlas 필요 경계: {'예' if session['risk_assessment']['requires_atlas'] else '아니오'}\n\n"
        sdoc += f"## 다음 문서\n\n- [[../flows/{stream_id}-focus|{flow_title}]]\n- [[../unknowns|모름과 경계]]\n- [[../atlas/index|Deep Atlas]]\n"
    else:
        sdoc += f"## Goal\n\n{session['expected_outcome']}\n\n## Stop condition\n\n{session['stop_condition']}\n\n## In scope\n\n" + bullets(session["scope"]["in_scope"], "- None")
    write(root, f"understanding/{session_id}.md", sdoc)

    # Focus flow note. This is a narrative, not the full implementation ledger.
    nodes = {n["id"]: n for n in focus_diagram.get("nodes", [])}
    primary = [nodes[x] for x in focus_diagram["reader_contract"]["primary_story_node_ids"]]
    fdoc = frontmatter("focus-flow", stream_id, stream.get("confidence", "PARTIAL"))
    fdoc += f"# {flow_title}\n\n{session['expected_outcome']}\n\n![[../excalidraw/{focus_diagram['id']}.excalidraw]]\n\n"
    if lang == "ko":
        fdoc += "## 30초 요약\n\n"
        fdoc += f"- 누가 시작하는가: {answers['who_starts']}\n- 무엇을 하려는가: {answers['what_they_want']}\n- 무엇을 판단하는가: {answers['key_decisions']}\n- 성공하면 무엇이 달라지는가: {answers['success_change']}\n\n"
        fdoc += "## 중심 흐름\n\n| # | 처리 | 의미 | 확인 상태 |\n|---:|---|---|---|\n"
        for n in primary:
            fdoc += f"| {n.get('step_number','')} | **{n['label'].split('. ',1)[-1]}** | {n.get('summary','')} | `{n.get('confidence','UNVERIFIED')}` |\n"
        fdoc += "\n## 왜 멈출 수 있는가\n\n" + bullets(focus_diagram["reader_contract"].get("stop_reasons", [])) + "\n\n"
        fdoc += "## 지금은 펼치지 않은 세부\n\n"
        collapsed = []
        for n in primary:
            collapsed.extend(n.get("collapsed_refs", []))
        fdoc += bullets([f"`{x}` · [[../atlas/flows/{stream_id}|Atlas에서 근거와 연결 확인]]" for x in collapsed], "- 생략된 중심 단계 없음")
        fdoc += "\n\n## 더 깊이 볼 때\n\n- [[../atlas/flows/" + stream_id + "|전체 단계·조건·상태·실패·보상]]\n- [[../unknowns|현재 미확인 사항]]\n"
    else:
        fdoc += "## Primary story\n\n" + "\n".join(f"{n.get('step_number')}. **{n['label']}**: {n.get('summary','')}" for n in primary)
    write(root, f"flows/{stream_id}-focus.md", fdoc)

    # Unknowns and scope boundary note.
    udoc = frontmatter("coverage-boundary", session_id, "PARTIAL")
    udoc += "# 아직 확인되지 않은 것과 현재 범위 밖 영역\n\n" if lang == "ko" else "# Unknown and out-of-scope boundaries\n\n"
    groups = [
        ("현재 답변·변경과 관련된 모름" if lang == "ko" else "Relevant unknowns", "unknown_relevant"),
        ("현재 목적에는 포함하지 않은 영역" if lang == "ko" else "Out of scope", "unknown_out_of_scope"),
        ("다음에 확장할 수 있는 지점" if lang == "ko" else "Expansion points", "expansion_points"),
    ]
    for title, key in groups:
        udoc += f"## {title}\n\n"
        items = coverage.get(key, [])
        if not items:
            udoc += "- 없음\n\n" if lang == "ko" else "- None\n\n"
        for item in items:
            udoc += f"<a id=\"{item['id']}\"></a>\n### {item['label']}\n\n- 이유: {item['reason']}\n- 영향: `{item['impact']}`\n- 다음 확인: {item.get('next_check') or '현재 목적에는 필요 없음'}\n- 신뢰도: `{item.get('confidence','UNVERIFIED')}`\n\n"
    udoc += "## 완료 판단\n\n"
    c = coverage["completion"]
    udoc += f"- 질문에 답했는가: `{c['question_answered']}`\n- stop condition 충족: `{c['stop_condition_met']}`\n- 변경 안전성: `{c['safe_to_change']}`\n- Atlas 권장: `{c['atlas_recommended']}`\n"
    write(root, "unknowns.md", udoc)

    vdoc = frontmatter("focus-visual-index", map_model["workspace_id"], "PARTIAL")
    vdoc += "# Focus visual index\n\n"
    for d in focus_visual.get("diagrams", []):
        vdoc += f"- [[excalidraw/{d['id']}.excalidraw|{d['title']}]]: {d['purpose']}\n"
    vdoc += "\n- [[atlas/visual-index|Deep Atlas visual index]]\n"
    write(root, "visual-index.md", vdoc)

    # Stable progression target. The detailed Atlas generator fills the linked directory.
    adoc = frontmatter("atlas-entry", map_model["workspace_id"], map_model.get("confidence", "PARTIAL"))
    adoc += "# Deep Atlas\n\n"
    adoc += "> Focus에서 답이 부족하거나, 위험한 변경·감사·인수·장애 분석이 필요할 때 엽니다.\n\n" if lang == "ko" else "> Open when Focus is insufficient or a risky change, audit, takeover, or incident requires full detail.\n\n"
    adoc += "- [[start-here|Atlas 시작]]\n- [[visual-index|Atlas 그림 목록]]\n- [[workspace-stream-map.canvas|Atlas Canvas]]\n"
    write(root, "atlas/index.md", adoc)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("map_model", type=Path)
    ap.add_argument("focus_visual_model", type=Path)
    ap.add_argument("understanding_session", type=Path)
    ap.add_argument("coverage", type=Path)
    ap.add_argument("output_root", type=Path)
    args = ap.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    generate(read_json(args.map_model), read_json(args.focus_visual_model), read_json(args.understanding_session), read_json(args.coverage), args.output_root)
    print(f"WROTE human-first Obsidian entry under {args.output_root}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
