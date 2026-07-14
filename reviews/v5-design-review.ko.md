# im-code-map v5 Focus/Atlas 설계·구현 검토

검토일: 2026-07-14

## 1. 최종 판단

v5는 별도의 “Simple 스킬”을 만들지 않고, **하나의 근거 모델에서 두 가지 투영을 생성**하도록 구성했다.

- **Focus**: 사용자의 한 질문을 기준으로 사람이 먼저 읽는 흐름. 기본 프로필이다.
- **Deep Atlas**: 상태, 오류, 보상, 도메인, 구현 근거를 포함한 상세 지도. v4의 상세 능력을 보존한다.

두 스킬을 분리하면 시간이 지나면서 축약판과 상세판이 서로 다른 사실을 말할 수 있다. v5는 `map-model.json`과 `evidence-ledger.json`을 공통 근거로 사용하고, 질문·범위·위험에 따라 표시 깊이만 바꾼다.

## 2. v4에서 바뀐 기본 계약

v4의 기본 질문은 “시스템 전체에는 어떤 흐름과 상태가 존재하는가?”에 가까웠다. v5의 기본 질문은 다음과 같다.

```text
누가 또는 무엇이 시작하는가?
→ 무엇을 하려는가?
→ 어떤 결정이 중요한가?
→ 어떤 데이터나 상태가 바뀌는가?
→ 성공 또는 중단이 어떻게 관찰되는가?
→ 지금 답에 필요한 모름과 범위 밖은 무엇인가?
```

따라서 전체 지도가 완성될 때까지 기다리지 않고, 한 가지 목적을 만족하는 흐름과 명시적인 경계를 먼저 제공한다. 상세 분석은 제거하지 않고 Atlas로 이동한다.

## 3. 추가된 이해 모델

### `understanding-session.json`

현재 분석이 왜 시작됐는지를 기록한다.

- 질문
- 독자
- 의도: `orient`, `trace`, `explain`, `before-change`, `debug`, `expand`
- 기대 결과
- 종료 조건
- 범위
- 위험 평가
- Focus/Atlas 라우팅 결정

### `coverage.json`

“모르는 것”을 한 덩어리로 뭉개지 않고 구분한다.

- `explored`: 실제 확인한 범위
- `unknown_relevant`: 현재 답이나 안전한 변경을 막는 모름
- `unknown_out_of_scope`: 이번 목적에서 의도적으로 제외한 영역
- `expansion_points`: 다음에 열어 볼 경계
- `boundaries`: Atlas 승격이 필요한 위험 경계

### `evidence-ledger.json`

Focus에서 짧게 표현한 카드도 코드·테스트·스키마·문서 근거로 되돌아갈 수 있게 한다. 간단한 그림이 사실의 간단한 버전으로 변질되지 않도록 하는 장치다.

## 4. Focus Excalidraw 보완

Focus 첫 화면에는 일반적으로 다음을 요구한다.

- 6~12개의 번호가 붙은 중심 단계
- 명확한 `START HERE`
- 한눈에 드러나는 정상 흐름과 성공 결과
- 최대 4개의 주요 판단
- 실패 상세 대신 “왜 흐름이 멈추는가” 요약
- 현재 관련 미확인 사항
- Deep Atlas로 가는 링크
- 업무 언어 중심 카드, 구현 식별자는 연결 문서로 이동

단계가 길어지면 한 줄로 계속 늘이거나 글자를 줄이지 않는다. **4개 카드 단위의 의미 단계 행**으로 접고, 모든 행을 왼쪽에서 오른쪽으로 읽고, 행 사이의 여백을 통해 다음 단계로 연결한다. 예제 주문 흐름은 다음처럼 나뉜다.

```text
1단계 주문 요청: 주문 요청 → 회원 자격 → 상품 주문 가능성 → 주문 접수
2단계 재고 확보: 재고 확보 → 수량 판단 → 재고 확보 완료 → 결제 승인 요청
3단계 결제·완료: 승인 판단 → 주문 결제 완료 → 후속 처리 알림 → 주문 완료
```

각 카드에 동일한 `PARTIAL` 또는 `UNVERIFIED` 표시를 반복하지 않는다. 불확실성은 근거 모델에는 그대로 보존하되, 사람 화면에서는 경계 카드와 미확인 문서에서 한 번에 설명한다.

아이콘은 제3자 아이콘 파일이나 특정 폰트에 의존하지 않고 Excalidraw 기본 도형으로 생성한다. 한국어 미리보기는 시스템에 존재하는 CJK 지원 폰트를 사용하며 폰트 파일은 패키지에 포함하지 않는다.

## 5. Deep Atlas 보존 범위

v4에서 강화한 다음 기능을 Atlas 프로필로 유지했다.

- actor, trigger, entry point, 업무 규칙과 권한
- 데이터 read/write와 상태 전이
- 정상·조건·비동기·오류·timeout·retry·cancel transition
- compensation과 observable outcome
- stream, 상태·자격, 도메인 책임 child Excalidraw
- child 파일을 합성한 master infinite canvas
- ExcalidrawAutomate 생성 스크립트
- 코드·테스트·스키마 근거
- 연결된 Obsidian 상세 지식 그래프

Atlas 산출물은 `architecture/atlas/` 아래에 모인다. v4 마이그레이션 과정에서도 상세 문서·그림·Canvas 경로를 이 위치로 정규화한다.

## 6. Obsidian 보완

Obsidian 시작 화면을 파일 종류가 아니라 **사용자의 질문 순서**로 바꿨다.

```text
start-here
→ 현재 이해 질문
→ Focus 흐름
→ 관련 미확인 사항
→ 필요한 경우 Deep Atlas
```

상세 Atlas에서는 stream을 중심으로 actor, domain, entity, state, rule, codebase, evidence가 연결된다. Focus Canvas와 Atlas Canvas를 분리해, 첫 화면에서 모든 연결을 강제로 보여 주지 않는다. 링크를 많이 만드는 것보다 읽는 길을 먼저 만드는 쪽이 인간에게 조금 더 친절하다. 소프트웨어 문서가 가끔 시도해 볼 만한 급진적 발상이다.

## 7. 위험과 자동 승격

다음 조건은 Atlas 승격 트리거다.

- 인증·권한
- 결제
- 개인정보
- 데이터 삭제
- 마이그레이션
- 동시성·중복 처리·idempotency
- retry·compensation
- 여러 저장소를 가로지르는 변경
- 근거 충돌
- 동적 dispatch
- 넓은 상태 변경
- 사용자의 명시적 전체 지도 요청

이해 목적이라면 Focus에서 해당 위치와 위험을 요약할 수 있다. 그러나 변경 승인, 구현, 검토 근거로는 Atlas가 필요하다. 번들 예제는 결제 경계가 있으므로 `PROFILE=focus`, `RISK=high`, `REQUIRES_ATLAS=true`를 동시에 반환한다. 모순이 아니라 “설명은 가능하지만 변경 승인은 아직 안 된다”는 구분이다.

## 8. 추가·변경된 주요 스크립트

### Focus와 라우팅

- `build_focus_profile.py`
- `route_profile.py`
- `generate_focus_obsidian_docs.py`
- `generate_focus_canvas.py`

### 모델 검증

- `validate_understanding_session.py`
- `validate_coverage.py`
- `validate_evidence_ledger.py`
- `validate_human_understanding.py`

### 마이그레이션

- `migrate_v4_to_v5.py`
- `migrate_v3_to_v5.py`

기존 Atlas 생성·합성·렌더링·링크 검증 스크립트는 v5 schema와 경로 구조에 맞게 유지·보완했다.

## 9. 최종 검증 결과

clean-room에서 패키지 내부 예제를 처음부터 다시 만들고 검사했다.

| 항목 | 결과 |
|---|---:|
| Python 스크립트 compile | 24개 PASS |
| JSON/Canvas/Excalidraw/Excalidrawlib parse | 46개 PASS |
| map-model | 3 streams, 오류 0, 경고 0 |
| understanding session | 오류 0, 의도된 위험 경고 1 |
| coverage | explored 4, relevant unknown 1, out of scope 2, 오류 0 |
| evidence ledger | 2 claims, 오류 0 |
| Focus visual model | 2 diagrams, 오류 0, 경고 0 |
| Focus Excalidraw | 2 files, 의미·가독성 오류 0 |
| Atlas visual model | 5 child diagrams, 오류 0, 경고 0 |
| Atlas Excalidraw | child 5 + master 1, 의미·가독성 오류 0 |
| Focus PNG/SVG | 각 2개 |
| Atlas PNG/SVG | 각 6개 |
| Obsidian Markdown | 38개 |
| Atlas Canvas | 30 nodes, 40 edges |
| Obsidian·Canvas·drawing 링크 | 오류 0, 경고 0 |
| deterministic Focus 재생성 | PASS |
| 전체 clean-room 생성 | PASS |
| v5.1 자체 stencil library | 14 items, PASS |
| v5.1 whiteboard representative | PASS |

의도된 경고는 다음 하나다.

```text
high-risk boundary is summarized in Focus;
Atlas is required before changing or approving it
```

이는 실패가 아니라 위험 경계가 정상적으로 작동했다는 확인이다.

## 10. 마이그레이션 검증

### v4 → v5

- 기존 map-model과 visual-model 보존
- schema `5.0.0` 변환
- Atlas reader contract 추가
- Focus 질문과 범위는 임의 생성하지 않고 재분석 필요 상태로 기록
- 상세 출력 경로를 `architecture/atlas/`로 정규화
- map, visual, session, coverage 검증 PASS

### Papercompany legacy 산출물 → v5

`701. Papercompany.zip`에는 앱 소스와 테스트가 없고 생성된 아키텍처 자료만 있다. 비메타데이터 파일 47개는 Markdown 27개, Excalidraw 14개, JSON 3개, Canvas 1개, 확장자 없는 파일 2개로 구성된다.

따라서 마이그레이션은 다음만 수행한다.

- domain 22개 보존
- legacy cross-domain path 4개를 불완전 stream으로 보존
- confidence `UNVERIFIED`
- actor, trigger, guard, 상태, 오류, retry, compensation을 추측하지 않음
- 상세 경로를 `architecture/atlas/`로 정규화

검증 결과 schema·stream 의미 검사는 PASS이며, 연결되지 않은 business domain 7개 경고는 기존 산출물의 불완전성을 드러내는 예상 결과다. Papercompany의 실제 업무 흐름을 인증하려면 원본 저장소, 테스트, 구성과 필요 시 런타임 근거를 대상으로 v5 분석을 다시 실행해야 한다.

## 11. 예제의 성격

commerce 예제는 Focus/Atlas 기능과 시각 구조를 검증하기 위한 **synthetic example**이다. Papercompany의 실제 규칙을 나타내지 않는다. 샘플이 그럴듯하다는 이유로 실제 시스템의 증거가 되는 기적은 이번 버전에도 구현하지 않았다.

## 12. 결론

v5의 핵심은 상세도를 줄이는 것이 아니다.

> 기계에는 넓은 근거를 보존하고, 사람에게는 현재 질문에 필요한 흐름과 경계를 먼저 보여 준다.

무한 캔버스와 상세 Atlas는 그대로 유지하되, 기본 시작점은 한 질문과 한 흐름이다. 이제 첫 화면은 코드베이스의 모든 연결을 자랑하는 대신, 사람이 실제로 읽고 다음 질문을 만들 수 있는 구조를 제공한다.
