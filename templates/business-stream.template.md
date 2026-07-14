# {{stream_name}}

Status: `{{confidence}}`  
Stream ID: `{{stream_id}}`

## 먼저 볼 것

- Stream diagram: ![[{{stream_excalidraw}}]]
- Master map: [[{{master_excalidraw}}]]
- Canvas: [[{{canvas_path}}]]

## 이 흐름이 답해야 하는 질문

> {{purpose}}

## 시작

| 항목 | 내용 |
|---|---|
| 행위자/시스템 | {{actors}} |
| Trigger | {{trigger_event}} |
| Entry point | `{{entry_point}}` |
| 시작 조건 | {{preconditions}} |
| 관련 도메인 | {{domains}} |

## 처리 흐름 한눈에 보기

```text
{{flow_ascii_summary}}
```

## 단계별 처리

| 순서 | 단계 | 수행 주체 | 도메인 | 읽기 | 쓰기 | 상태 변화 | 규칙/조건 | 근거 | 신뢰도 |
|---:|---|---|---|---|---|---|---|---|---|
| {{order}} | {{step}} | {{actor}} | {{domain}} | {{reads}} | {{writes}} | {{state_change}} | {{rule_or_condition}} | {{evidence}} | {{confidence}} |

## 분기와 전이

| From | To | 종류 | 화살표 라벨 | 실제 조건 | 근거 | 신뢰도 |
|---|---|---|---|---|---|---|
| {{from_step}} | {{to_step}} | {{transition_kind}} | {{label}} | `{{condition}}` | {{evidence}} | {{confidence}} |

모든 decision은 최소 두 개의 조건부 전이를 가져야 한다. `성공/실패`처럼 의미가 비어 있는 라벨만 쓰지 않는다.

## 종료 결과

| 결과 | 유형 | 종료 단계 | 외부에서 관찰되는 결과 |
|---|---|---|---|
| {{outcome}} | {{outcome_type}} | {{terminal_step}} | {{observable_result}} |

## 오류, 타임아웃, 재시도

| 발생 지점 | 오류/조건 | 처리 단계 | 재시도 정책 | 최종 결과 |
|---|---|---|---|---|
| {{error_from}} | {{error}} | {{handler}} | {{retry_policy}} | {{terminal_outcome}} |

## 보상 처리

| Trigger | 보상 작업 | 복구되는 자원/상태 | 보상 실패 시 처리 |
|---|---|---|---|
| {{compensation_trigger}} | {{compensation_action}} | {{restores}} | {{compensation_failure}} |

## 상태 변화 요약

- {{state_change_summary}}

## 연결된 지식

- Actors: {{actor_links}}
- Domains: {{domain_links}}
- Entities: {{entity_links}}
- State machines: {{state_links}}
- Rules: {{rule_links}}
- Codebases: {{codebase_links}}

## 증거

| 주장 | Source | Locator | Tool | Captured at | 신뢰도 |
|---|---|---|---|---|---|
| {{claim}} | `{{source}}` | `{{locator}}` | {{tool}} | {{captured_at}} | {{confidence}} |

## 확인 불가 / 충돌

- {{uncertainty}}
