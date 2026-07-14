# {{state_machine_name}}

Status: `{{confidence}}`  
State machine ID: `{{state_machine_id}}`  
Entity: [[{{entity_note}}]]

## 먼저 볼 그림

![[{{state_diagram}}]]

## 상태 정의

| 상태 | 의미 | Terminal | 허용/차단되는 동작 | 근거 |
|---|---|---:|---|---|
| {{state}} | {{meaning}} | {{terminal}} | {{behavior}} | {{evidence}} |

## 전이

| From | To | Trigger | Guard | Effect | 관련 stream/step | 신뢰도 |
|---|---|---|---|---|---|---|
| {{from_state}} | {{to_state}} | {{trigger}} | `{{guard}}` | {{effect}} | [[{{stream_note}}]]#{{step_ref}} | {{confidence}} |

## 불법 또는 확인되지 않은 전이

- {{invalid_or_unknown_transition}}

## 근거

- {{evidence}}
