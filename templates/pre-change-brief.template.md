# Before Change Brief

Generated at: {{generated_at}}

## 수정 요청

{{request_rewrite}}

## 먼저 볼 그림

- Impact diagram: `{{before_change_excalidraw}}`
- Related domain overview: `{{domain_overview_excalidraw}}`
- Related business stream: `{{business_stream_excalidraw}}`

## 관련 도메인

- Primary: {{primary_domain}}
- Secondary: {{secondary_domains}}
- Cross-cutting: {{cross_cutting_domains}}

## 관련 codebase

| Codebase | 역할 | 수정 여부 | 근거 |
|---|---|---:|---|
| {{codebase_id}} | {{role}} | {{will_change}} | {{evidence}} |

## 수정 대상

- 파일: {{target_files}}
- 함수/클래스: {{target_symbols}}
- API/화면: {{target_api_or_ui}}

## 영향 가능 범위

- 호출자: {{callers}}
- 호출 대상: {{callees}}
- 연결 도메인: {{affected_domains}}
- 연결 codebase: {{affected_codebases}}
- 데이터 엔티티: {{data_entities}}
- 테스트: {{tests}}

## 건드리지 않을 영역

- {{do_not_touch}}

## 구조 경계

- UI는 DB에 직접 접근하지 않는다.
- Controller/Route는 비즈니스 로직을 직접 소유하지 않는다.
- Service는 UI 컴포넌트를 import하지 않는다.
- Repository는 HTTP 요청 객체를 알지 않는다.
- 테스트 전용 helper를 production 코드에서 import하지 않는다.
- cross-codebase 호출 방식은 API, event, queue, package boundary 중 무엇인지 명시한다.

## 확인한 근거

- {{evidence}}

## 실행할 테스트

```bash
{{test_commands}}
```

## 갱신할 문서/지도

- {{docs_and_maps}}

## 신뢰도

{{confidence}}
