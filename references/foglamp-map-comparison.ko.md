# Foglamp 비교를 통한 im-code-map v5.3 개선 검토

## 기준

- 비교 대상: `foglamp-labs/foglamp@0021f51d09a7d6910cc4e36f9eabaabc1d31e568`
- 개선 대상: `im-code-map v5.2.1 → v5.3.0`
- 범위: codebase scan 계약, map projection, layout, edge routing, card design, 상세 정보 연결 방식

Foglamp는 AI 사용 구조를 24개 이하의 노드로 요약해 고정 웹 렌더러에서 보여 주는 제품이다. im-code-map은 일반 코드베이스의 업무 흐름, 상태, 규칙, 오류, 보상, 코드 근거를 Obsidian과 Excalidraw에 남기는 이해·인수·변경 분석 도구다. 목적이 다르므로 Foglamp를 복제하지 않고 지도 생성 원칙만 선별했다.

## 비교표

| 항목 | Foglamp | im-code-map v5.2.1 | v5.3 결정 |
|---|---|---|---|
| 최초 지도 목적 | 공유 가능한 고수준 AI flow | Focus와 Atlas를 모두 생성 | 최초 지도는 bounded overview로 분리 |
| 데이터 계약 | 작고 엄격한 단일 graph JSON | 상세 semantic model과 visual model | 상세 모델 뒤에 별도 overview projection 추가 |
| 노드 제한 | 최대 24 | Focus에도 절대 상한이 약함 | Overview 최대 24, 권장 12~20 |
| 엣지 제한 | 최대 48 | 상세 분기와 근거가 그대로 노출될 수 있음 | Overview 최대 48, 권장 18~36 |
| 라벨 제한 | node 28, sub 40, edge 24 | 일부 설명 카드가 길어짐 | node 28, sub 44, edge 24 강제 |
| 스타일 소유권 | renderer가 색·아이콘·좌표 소유 | 생성 모델과 renderer 책임이 섞일 수 있음 | semantic model에서 좌표·색상 제거 |
| 배치 | ELK layered, root LTR | diagram type별 수동 규칙이 많음 | group-first deterministic layout |
| 긴 pipeline | group을 세로 stack으로 접음 | 캔버스가 넓어지거나 snake가 생길 수 있음 | 2~6개 node의 vertical group, group은 LTR |
| leaf node | model/tool을 owner card에 fold | 도구·규칙·상태가 별도 노드가 되어 선이 늘 수 있음 | model/tool/rule/state/evidence/technology 최대 4개 embed |
| cross-group edge | group boundary로 모아 macro story 유지 | 세부 node edge가 모두 드러남 | channel 공유와 overview edge dedupe 권장 |
| edge routing | orthogonal + rounded corner | 일부 도식은 카드 근처에서 꺾임이 불규칙 | orthogonal-rounded 고정, recovery는 아래 channel |
| edge label | 가장 긴 열린 segment에 배치 | edge 중간점 또는 임의 위치 | longest-segment anchor + 흰 pill 배경 |
| 작은 지도 | 중앙 fit | 경우에 따라 여백 과다 | readable scale로 중앙 정렬 |
| 긴 지도 | 지나치게 축소하지 않고 시작점부터 열기 | master 전체를 한 번에 맞출 수 있음 | overview는 시작점 우선, Atlas는 child 링크 사용 |
| 상세 정보 | click detail popover | Obsidian note와 child drawing | overview detail/link/evidenceRefs로 이동 |
| 증거·불확실성 | 고수준 요약 중심 | evidence ledger와 coverage가 강점 | 그대로 유지, overview에서 삭제하지 않고 링크 |
| 공개 업로드 | public unlisted URL 생성 | 로컬 Obsidian 중심 | 업로드 기능을 도입하지 않음 |

## 핵심 개선점

### 1. 분석 모델과 지도 모델을 분리

이전에는 상세하게 분석할수록 그림도 복잡해질 가능성이 있었다. v5.3은 상세 모델을 먼저 만든 뒤 사람이 처음 볼 정보만 `overview-map.json`으로 투영한다.

```text
상세 분석이 많아짐
≠ 첫 그림의 노드가 무한히 많아짐
```

### 2. 중요한 흐름을 먼저 보존

projection은 다음 순서로 node를 보존한다.

1. entry와 outcome
2. 질문에 답하는 focus path
3. decision, high-risk boundary, external call, data store
4. focus path에 붙은 error/recovery endpoint
5. 나머지는 importance와 연결성으로 선택

### 3. leaf capability 접기

다음 정보는 독립적인 업무 단계가 아니라면 owner card 안의 작은 chip으로 접는다.

- model
- tool
- rule
- state
- evidence
- technology

상세 코드 경로와 근거는 사라지지 않고 `detail`, `evidenceRefs`, Obsidian note에 남는다.

### 4. 고정 renderer

분석 Agent는 다음을 결정하지 않는다.

- x/y 좌표
- 카드 색상
- 아이콘 도형
- edge route
- font size

같은 overview JSON은 같은 Excalidraw scene과 SVG를 생성한다.

### 5. Excalidraw clean v2

- off-white canvas
- 얇은 neutral group surface
- white node card
- 4px semantic accent
- 작은 native vector icon
- title 16px, sub 11px
- neutral normal edge
- conditional/async/data/error/recovery에만 의미색 사용
- 그림자와 채색 면적 최소화
- raw UUID·symbol·path를 overview에서 제거

## 도입하지 않은 Foglamp 요소

- AI 전용 node kind만 사용하는 방식
- 모든 상세 지도를 24 node로 제한하는 방식
- hosted public upload와 edit token
- network favicon 의존성
- evidence/unknown/state/error를 제거한 홍보용 축약
- Foglamp React/ELK 소스의 직접 복사

Foglamp 저장소는 Apache-2.0이지만 v5.3 구현은 개념만 참고해 Python과 native Excalidraw primitive로 독립 작성했다.

## 새 파일

```text
schemas/overview-map.schema.json
scripts/overview_map_core.py
scripts/build_bounded_overview_map.py
scripts/validate_bounded_overview_map.py
scripts/clean_map_renderer.py
scripts/render_clean_excalidraw_map.py
scripts/build_clean_map_bundle.py
scripts/polish_excalidraw.py
scripts/validate_clean_excalidraw.py
templates/excalidraw-clean-v2.json
references/execution-entry-contract.md
references/clean-excalidraw-map-design.md
```

## 남은 한계

- Excalidraw는 Foglamp 웹 UI처럼 클릭 시 BFS path를 동적으로 강조하지 않는다. 대신 focus path 번호, child drawing link, Obsidian 탐색을 사용한다.
- legacy Atlas scene의 post-processor는 스타일만 정리하며 잘못된 좌표 자체를 고치지는 않는다.
- 복잡한 cyclic graph는 overview에서 main story와 recovery channel로 투영되므로, 모든 cycle을 보려면 Atlas가 필요하다.
