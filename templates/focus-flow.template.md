---
type: focus-flow
profile: focus
stream: "{{stream_id}}"
confidence: "{{confidence}}"
---

# {{flow_title}}

## 30초 요약

- 누가 시작하는가: {{who_starts}}
- 무엇을 하려는가: {{what_they_want}}
- 무엇을 판단하는가: {{key_decisions}}
- 성공하면 무엇이 달라지는가: {{success_change}}

## 중심 흐름

| # | 처리 | 의미 | 확인 상태 |
|---:|---|---|---|
| {{n}} | {{label}} | {{summary}} | `{{confidence}}` |

## 왜 멈출 수 있는가

- {{stop_reason}}

## 아직 확인되지 않은 것

- {{unknown_relevant}}

## 더 깊이 보기

- [[../atlas/flows/{{stream_id}}|전체 단계·조건·상태·실패·보상·코드 근거]]
