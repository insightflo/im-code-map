# im-code-map v3 및 Papercompany 산출물 검토·보완 보고서

- 검토일: 2026-07-10
- 검토 대상 스킬: `im-code-map-skill-v3 3.zip`
- 검토 대상 산출물: `701. Papercompany.zip`
- 보완 결과: `im-code-map v4.0.0`

## 1. 결론

기존 v3의 핵심 문제는 Excalidraw의 그림 솜씨보다 **그림 앞단의 의미 모델이 업무 스트림을 표현하지 못한다는 점**이었다. 스킬 문서에는 “flow”와 swimlane이 언급되어 있지만, 실제 `map-model`과 `visual-model`에는 다음을 강제하는 구조가 없었다.

- 누가 시작하는가
- 어떤 요청·이벤트·스케줄이 시작점인가
- 어떤 권한·자격·상태·정책을 검사하는가
- 어떤 데이터를 읽고 쓰는가
- 어떤 상태가 무엇으로 바뀌는가
- 성공·거절·실패·취소·재시도·보상은 어디서 끝나는가
- 각 판단과 상태 변화의 코드 근거가 무엇인가

그래서 `회원 → 상품 → 주문`처럼 “서로 관련 있다”는 수준의 도메인 관계도는 만들 수 있었지만, “어떤 회원이 어떤 조건에서 어떤 상품을 주문할 수 있고, 재고·결제 실패 시 무엇을 되돌리는가”를 한 줄기로 읽을 수 없었다. 그림 생성기에게 업무 규칙을 주지 않고 업무 흐름을 그리라고 한 셈이다. 인간은 흔히 출력 장식을 고치며 입력 모델 문제를 해결하려고 하지만, 이번에는 그 유서 깊은 실수를 피했다.

v4는 이를 다음 구조로 바꿨다.

1. **업무 스트림을 1급 모델로 정의**한다.
2. **행위자, 트리거, 진입점, 규칙, 엔티티 상태, 분기, 오류, 재시도, 보상, 종료 결과**를 구조화한다.
3. 스트림·상태·도메인 그림을 각각 child Excalidraw로 만들고, 이를 **하나의 master infinite canvas에 영역별로 합성**한다.
4. 모든 의미 노드에 **네이티브 Excalidraw 벡터 픽토그램**을 붙인다.
5. Obsidian을 개별 문서 보관함이 아니라 **스트림 중심 연결 그래프**로 생성한다.
6. JSON 유효성만으로 완료하지 않고 **SVG/PNG 렌더링 → 육안 점검 → 재생성**을 필수화한다.

## 2. 검토 범위와 한계

`701. Papercompany.zip`에는 `architecture/` 산출물만 있고 Papercompany 원본 소스 저장소는 포함되지 않았다. 따라서 산출물 안의 “VERIFIED” 주장과 코드 라인 번호를 제가 원본 코드에서 독립적으로 재검증하는 것은 **확인할 수 없습니다**.

이번 검토에서 확인한 것은 다음 두 가지다.

- v3 스킬 자체의 스키마·생성기·검증기 구조
- Papercompany 산출물이 그 구조와 얼마나 일치하며, 사람이 실제 업무 흐름으로 읽을 수 있는지

Papercompany를 v4로 완전히 재작성하려면 원본 저장소에서 CodeGraph와 소스·테스트를 다시 실행해야 한다. 이번 패키지에는 기존 정보를 임의로 사실화하지 않고, 22개 도메인과 4개 경로 요약만 `UNVERIFIED` 이관한 재분석 골격을 별도로 제공한다.

## 3. v3 스킬의 구조적 결함

### 3.1 `flows[].steps`가 자유 형식 객체였다

근거 파일: `templates/map-model.schema.json`

v3의 `flow`는 `id`, `name`, `domain_ids`, `steps`, `evidence`, `confidence` 정도만 요구한다. 특히 `steps.items`가 단순 `object`여서 아래 항목이 존재하지 않아도 스키마가 막지 못한다.

- actor / role / member type
- trigger / entry point
- decision / guard / branch condition
- read / write / command / query / event
- entity state before / after
- timeout / retry / cancellation
- compensation
- observable terminal outcome

따라서 “step 이름 몇 개가 배열에 있다”와 “업무 스트림이 완성되었다”를 구분할 수 없었다.

### 3.2 visual node 종류가 구조 박스 중심이었다

근거 파일: `templates/visual-model.schema.json`

v3 node kind는 `domain`, `codebase`, `ui`, `api`, `service`, `repository`, `storage`, `external`, `event`, `worker`, `test`, `risk`, `note` 등에 집중되어 있다. 다음 업무 의미가 없다.

- start / end
- decision
- state-change
- error-handler
- compensation
- wait / timeout

edge도 `from`, `to`, `label`, `direction` 정도라서, 분기 조건이나 정상·오류·재시도·비동기·보상 경로를 기계적으로 구분할 수 없었다.

### 3.3 생성기가 안정적인 업무 도식 생성기가 아니었다

근거 파일: `scripts/generate_excalidraw_from_visual_model.py`

v3 생성기는 시간값과 난수를 이용해 element ID와 seed를 만들고, 기본적으로 rectangle/text/arrow를 배치한다. 이 방식에는 다음 문제가 있다.

- 같은 입력을 다시 생성해도 diff가 커질 수 있음
- 노드 종류에 따른 시각 문법이 없음
- 판단·상태·오류·보상을 모양으로 구분하지 못함
- child 파일과 master 파일의 안정적 합성 규칙이 없음
- 렌더링 결과를 검사하지 않음

### 3.4 “15개가 넘으면 파일 분리”만 있고 재결합 규칙이 없었다

v3는 큰 그림을 하위 Excalidraw로 나누도록 안내했지만, 분리한 파일을 master infinite canvas에 다시 배치하고 child 원본 링크를 유지하는 명시적 합성 모델이 없었다. 결과적으로 도메인별 파일은 늘어나지만, 독자는 어느 파일부터 읽고 다음에 무엇으로 이동할지 다시 추리해야 했다. 문서를 많이 만들면 이해가 자동으로 늘어난다는 인간 사회의 기묘한 믿음이 여기에도 스며들어 있었다.

## 4. Papercompany 산출물에서 확인한 문제

세부 수치는 `papercompany-v4-review/audit-metrics.json`에 기록했다.

### 4.1 map-model이 v3 스키마와 일치하지 않는다

Papercompany `architecture/map-model.json`의 최상위 키는 다음이다.

```text
schema_version, workspace_id, generated_at,
analysis_basis, product_model, domains, cross_domain_flows
```

반면 v3 schema가 요구하는 14개 키 가운데 다음 10개가 없다.

```text
source_tools, confidence, tool_status, documentation_provider,
codebases, domain_edges, flows, visual_outputs, risks, uncertainties
```

또 `analysis_basis`, `product_model`, `cross_domain_flows`는 v3 schema의 정식 필드가 아니다.

`jsonschema.Draft202012Validator`로 검사한 결과:

- map-model 오류: **76개**
  - required 오류 54개
  - enum 오류 22개

오류 수는 중첩 객체의 연쇄 오류를 포함하므로 “서로 독립적인 결함이 정확히 76개”라는 뜻은 아니다. 다만 현재 파일이 제공된 v3 schema의 유효한 인스턴스가 아니라는 점은 명확하다.

### 4.2 visual-model은 실제 그림을 재생성할 정보가 거의 없다

Papercompany `architecture/visual-model.json`에는 diagram 항목이 14개 있다.

- node가 있는 diagram: **1개**
- node가 없는 diagram: **13개**
- 빈 node 비율: `13 ÷ 14 × 100 = 92.9%`
- edge가 있는 diagram: **0개**
- edge가 없는 비율: `14 ÷ 14 × 100 = 100%`
- 전체 visual node: **6개**
- 전체 visual edge: **0개**

`jsonschema.Draft202012Validator` 결과는 **98개 오류**였다.

- required 오류 84개
- type 오류 6개
- enum 오류 8개

특히 diagram의 `type` 대신 `kind`를 쓰거나, `type: Business`, `type: Platform`, `type: Cross-cutting`처럼 v3 schema가 허용하지 않는 값을 사용한 항목이 있다.

실제 `.excalidraw` 파일 14개에는 화살표가 들어 있지만 `visual-model`에는 edge가 하나도 없다. 따라서 현재 기계 모델만으로 그 그림들을 동일하게 재생성할 수 없다. 즉, **모델과 최종 그림 사이의 추적 가능성이 끊겨 있다**. 그림이 존재한다는 사실과 재현 가능한 아키텍처 모델이 존재한다는 사실은 서로 다르다. 파일 확장자가 그 차이를 대신 해결해 주지는 않는다.

### 4.3 흐름 그림도 조건·상태·종료가 부족하다

실제 Excalidraw 파일 수는 14개다. 대표 파일의 element 구성은 다음과 같다.

| 파일 | 전체 element | rectangle | arrow | text |
|---|---:|---:|---:|---:|
| `system-overview` | 36 | 12 | 10 | 14 |
| `heartbeat-lifecycle-flow` | 30 | 10 | 4 | 16 |
| `workflow-dag-flow` | 30 | 8 | 6 | 16 |
| `runtime-domain-map` | 9 | 4 | 0 | 5 |

박스와 화살표가 있다는 점은 확인되지만, 판단 노드·조건 라벨·상태 전이·오류 종료·재시도·보상 경로가 일관된 시각 문법으로 모델링되지 않았다. `heartbeat-lifecycle-flow` 같은 이름에도 화살표가 4개뿐이며, 문서에 적힌 풍부한 예외 분류·복구·취소 정보를 흐름으로 따라갈 수 없다.

### 4.4 Obsidian이 연결 그래프로 작동하지 않는다

Papercompany의 domain Markdown 문서는 22개다.

- Obsidian wikilink `[[...]]` 총계: **0개**
- 일반 Markdown 링크 총계: **27개**
- Canvas: node 26개, edge 18개
  - file node 17개
  - text node 9개

일부 문서가 overview 그림과 Canvas로 연결되지만, 스트림→행위자→규칙→상태→도메인→코드 근거로 이어지는 상호 연결은 없다. 개별 문서의 내용은 상당히 상세한데, 그 상세함이 그래프로 조립되지 않았다. 독자는 훌륭한 문서 여러 편을 받지만 여전히 전체 업무를 자기 머릿속에서 수동 조립해야 한다.

## 5. v4에서 보완한 내용

### 5.1 업무 스트림 발견 절차

도메인 이름을 연결해 흐름을 만들지 않는다. 다음 순서로 후보를 찾는다.

1. 사용자 의도, API, 이벤트, 스케줄, CLI, 메시지, 복구 작업 등 trigger를 수집한다.
2. 각 trigger의 성공·거절·실패·취소·부분 성공 결과를 수집한다.
3. 실제 entry point에서 시작해 판단, 데이터 읽기/쓰기, 상태 변화, 외부 호출, 비동기 경계, 종료 결과까지 추적한다.
4. 독립적인 trigger나 업무 결과가 있는 경우에만 child stream으로 분리한다.
5. 동일한 업무 의도와 규칙을 구현하는 기술 경로는 중복 스트림으로 부풀리지 않는다.
6. 사용자 가치, 운영 중요도, 상태 변경, 도메인 횡단 범위로 우선순위를 정한다.

또 한 단계 안에서도 두 층을 분리한다.

- 업무 층: 의도, 권한, 규칙, 상태, 가치, 실패, 결과
- 구현 층: route, handler, symbol, job, queue, table, event, test

Excalidraw에는 업무 행동을 먼저 쓰고, 함수명·경로·증거는 링크된 Obsidian note와 `implementation_refs`에 둔다.

### 5.2 map-model v4

추가된 1급 객체:

- `actors`
- `entities`
- `state_machines`
- `business_rules`
- `domain_interactions`
- `business_streams`

각 stream step은 다음을 갖는다.

- actor/domain
- step kind
- action
- input/output
- read/write
- state changes
- rule references
- implementation references
- evidence/confidence

transition은 정상, 조건, 비동기, retry, error, timeout, compensation, cancel을 구분한다.

### 5.3 stream 완결성 gate

다음 중 하나라도 발생하면 stream은 실패한다.

- actor·trigger·entry point 없음
- start 또는 terminal outcome 없음
- decision branch가 2개 미만
- branch condition이 비어 있음
- start에서 도달할 수 없는 step이 있음
- end step에서 다시 일이 진행됨
- state change가 알 수 없는 entity/state를 참조함
- external call의 실패 동작을 고려하지 않음
- 필요한 compensation이 모델에 없음

### 5.4 Excalidraw child + master composition

v4 visual hierarchy:

1. domain responsibility/context child
2. primary business-stream child
3. state/eligibility child
4. supporting/alternate stream child
5. 모든 child를 영역별로 합친 master infinite canvas

child 파일이 유지보수 원본이다. master는 child를 복제·배치한 생성 뷰이며, 각 영역에 원본 child 링크가 있다. 개별 그림과 전체 지도를 모두 얻되, 둘 중 하나를 수동으로 동기화하는 고행은 요구하지 않는다.

### 5.5 의미 중심 벡터 아이콘

모든 주요 node에 네이티브 Excalidraw primitive로 만든 픽토그램을 넣었다.

- start / end
- decision
- state change
- event
- data / storage
- external system
- error
- compensation
- domain / codebase / test

emoji는 플랫폼별 글꼴·크기·렌더링 차이가 커서 production icon으로 사용하지 않는다. 아이콘은 텍스트를 대신하지 않고, shape와 label을 빠르게 구분하게 돕는다. validator는 의미 node에 native vector icon이 없거나 text/emoji icon을 쓰면 실패한다.

### 5.6 렌더 기반 시각 QA

검증 순서:

```text
generate
→ schema/semantic validation
→ Excalidraw output validation
→ SVG/PNG render
→ primary/master/state/error-heavy preview inspection
→ refine and re-render
```

validator가 확인하는 항목에는 다음이 포함된다.

- stable ID와 유효한 binding
- start/end/decision branch
- branch condition
- isolated node
- end node outgoing edge
- node overlap
- 최소 글꼴 크기와 label 길이
- frame child ordering
- native vector semantic icon
- master child-link와 composition reference

### 5.7 Obsidian을 스트림 중심 그래프로 재구성

생성 구조:

```text
architecture/
  start-here.md
  visual-index.md
  workspace-stream-map.canvas
  flows/
  actors/
  domains/
  entities/
  states/
  rules/
  codebases/
  indexes/
  excalidraw/
  excalidraw-automate/
  machine/
```

flow note가 주 문서가 되며, actor/domain/entity/state/rule/codebase와 서로 링크된다. Excalidraw child가 flow note에 embed되고, Canvas는 stream·state/rule·domain·evidence를 연결한다.

## 6. 포함 예제로 확인한 실제 형태

v4 예제는 “검증된 회원이 상품을 주문한다”는 합성 예제다. 다음 순서가 한 흐름으로 보인다.

```text
회원 주문 제출
→ 회원 역할·VERIFIED 상태·정지 여부 검사
→ 상품 상태·판매 기간·가격 조회
→ 주문 가능 여부 판단
→ Order NONE → PENDING
→ 재고 조건부 예약
→ Order PENDING → RESERVED
→ 결제 승인 요청
→ Order RESERVED → PAID
→ order.placed event 발행
→ PAID 주문 반환
```

별도 종료 경로:

- 회원 부적격: 주문 생성 없이 거절
- 상품 비활성/판매기간 종료: 주문 생성 없이 거절
- 재고 부족: Order PENDING → FAILED, 결제 미호출
- 결제 거절/timeout: 재고 해제 compensation, Order FAILED

이 예제의 조건은 Papercompany의 실제 업무 규칙이 아니라, v4가 요구한 의미를 검증하기 위한 명시적 synthetic source snapshot에 기반한다.

## 7. 검증 결과

최종 clean-room validator 결과:

- Python script compile: **13개 통과**
- map-model: **3 streams, error 0, warning 0**
- visual-model: **5 child diagrams, error 0, warning 0**
- Excalidraw: `5 child + 1 master = 6개`, error 0, warning 0
- SVG preview: **6개**
- PNG preview: **6개**
- ExcalidrawAutomate script: **4개**
- Obsidian Markdown note: **32개**
- JSON Canvas: **30 nodes, 40 edges**
- Obsidian/Canvas/Excalidraw link validation: error 0, warning 0
- 전체 패키지: **end-to-end PASS**

검증은 번들 산출물의 존재만 보는 것이 아니라 임시 빈 디렉터리에서 모델→child 그림→master→preview→Obsidian→Canvas를 다시 생성하는 방식으로 수행했다.

## 8. Papercompany 이관 결과와 남은 작업

제공한 `papercompany-v4-review`에는 다음이 있다.

- `map-model.v4.migrated.json`
- `migration-report.md`
- `audit-metrics.json`
- `README.ko.md`
- `stream-reanalysis-matrix.ko.md`

이관 결과:

- domain: **22개 유지**
- legacy cross-domain path: **4개를 incomplete stream으로 유지**
- confidence: **UNVERIFIED**
- v4 map validator: error 0, warning 7
- warning 7개는 stream에 연결되지 않은 business domain이다.

이관한 4개 후보:

1. `heartbeat-cycle`
2. `workflow-run`
3. `mission-supervision`
4. `cross-company-delegation`

각 후보는 기존 path label만 보존하며 actor, trigger, entry point, guard, state transition, error, retry, compensation, outcome을 새로 꾸며내지 않는다. 원본 저장소에서 재분석해야만 child stream diagram과 master Papercompany map을 승인할 수 있다.

## 9. 최종 판단

이번 문제는 “Excalidraw를 조금 더 예쁘게” 만드는 것으로 해결되지 않는다. 기존 시스템은 업무 흐름을 그릴 데이터가 없었고, 결과 파일과 모델 사이도 끊겨 있었다.

v4는 다음 요구를 직접 충족한다.

- 도메인 관계가 아니라 시작부터 종료까지 읽히는 업무 stream
- 회원 유형·권한·상품 상태·정책·재고·결제 같은 조건 표현
- 상태 전이와 실패·재시도·보상 경로 표현
- child 파일을 master infinite canvas에 합성
- 직관적인 semantic vector icon
- Obsidian의 양방향 연결과 embed를 활용한 stream 중심 탐색
- 모델·그림·문서·Canvas의 재현 가능한 단일 파이프라인
- 원본 근거가 없을 때 `UNVERIFIED`로 남기는 정직한 migration

따라서 v3의 소규모 패치가 아니라 schema와 생성 계약을 바꾸는 **v4.0.0 breaking upgrade**로 처리한 것이 타당하다.
