# {{rule_name}}

Status: `{{confidence}}`  
Rule ID: `{{rule_id}}`  
Type: `{{rule_type}}`

## 규칙

```text
{{condition}}
```

## 결과

- Pass: {{pass_outcome}}
- Fail: {{fail_outcome}}

## 적용 범위

- Scope: {{scope}}
- Business streams: {{stream_links}}
- Entities: {{entity_links}}
- Decision nodes: {{decision_links}}

## 구현과 테스트 근거

| Source | Locator | 주장 | 신뢰도 |
|---|---|---|---|
| `{{source}}` | `{{locator}}` | {{claim}} | {{confidence}} |

## 주의

문서나 이름만으로 조건식을 재구성하지 않는다. 실제 비교식, 정책 함수, 스키마 제약, 테스트 또는 런타임 증거가 없으면 `UNVERIFIED`로 표시한다.
