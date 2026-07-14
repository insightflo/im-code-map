# {{domain_name}}

Status: `{{confidence}}`  
Domain ID: `{{domain_id}}`  
Type: `{{domain_type}}`

## 한 줄 책임

{{purpose}}

## 먼저 읽을 업무 흐름

| Business stream | 이 도메인의 역할 | 관련 actor | 상태/규칙 | 신뢰도 |
|---|---|---|---|---|
| [[{{stream_note}}]] | {{domain_role_in_stream}} | {{actors}} | {{states_and_rules}} | {{confidence}} |

도메인 설명은 여기서 끝나지 않는다. 위 stream 링크가 비어 있다면 business domain coverage가 실패한 것이다.

## 소유 책임

- {{responsibility}}

## 소유 엔티티와 상태

- Entity: [[{{entity_note}}]]
- State machine: [[{{state_machine_note}}]]

## 다른 도메인과의 계약

| 상대 도메인 | 종류 | 방향 | Contract | 동기/비동기 | 사용 stream | 근거 |
|---|---|---|---|---|---|---|
| [[{{target_domain_note}}]] | {{interaction_type}} | {{direction}} | `{{contract}}` | {{mode}} | [[{{stream_note}}]] | {{evidence}} |

## 구현 codebase

| Codebase | 역할 | 주요 경로/심볼 | Entrypoint | 신뢰도 |
|---|---|---|---|---|
| [[{{codebase_note}}]] | {{role}} | `{{paths}}` | `{{entry_point}}` | {{confidence}} |

## 그림

- Responsibility map: [[{{domain_overview_excalidraw}}]]
- Participating stream diagrams: {{stream_diagram_links}}
- Master map: [[{{master_excalidraw}}]]

## 근거

- {{evidence}}

## 위험과 확인 불가

- {{risk_or_uncertainty}}
