# Papercompany 핵심 stream 재분석 매트릭스

아래 네 stream 이름과 path는 기존 `architecture/map-model.json`의 `cross_domain_flows`에서 보존한 것이다. 표의 “확인 항목”은 사실 주장이나 완성된 규칙이 아니라, 원본 저장소에서 반드시 추출해야 할 질문이다.

## 1. `heartbeat-cycle`

기존 path:

```text
heartbeat-scheduler(3-lane)
→ atomic checkout(work-tracking) + budget preflight(cost-budget)
→ execute via adapter(adapter-runtime)
→ artifact extraction(work-products)
→ release
```

| 구분 | 원본 코드에서 확인할 항목 |
|---|---|
| Actor/trigger | timer, routine, recovery, on-demand 중 실제 trigger 종류와 각 시작 주체 |
| Entry point | scheduler tick, route, queue, recovery job 등 구체적인 진입 symbol |
| Preconditions | agent 상태, active run, budget, workspace, authentication, queue eligibility |
| Decisions | 실행 가능/보류/거절/복구 분기와 실제 조건식 |
| State | heartbeat run, workspace checkout, budget scope, artifact/work product의 전이 |
| Async boundary | adapter child process, event/log, artifact collection이 동기인지 비동기인지 |
| Failure | timeout, cancel, overload, quota, auth, command, adapter 실패의 실제 처리 |
| Retry/recovery | 재시도 주체, backoff, stale/orphan 기준, 최대 시도, idempotency |
| Compensation | checkout·budget·workspace·session 자원을 어떤 순서로 release하는지 |
| Outcomes | 실행 완료, 실행 거절, queue 유지, recovery 완료, permanent failure의 관측 결과 |
| 권장 child diagrams | scheduler lanes, one heartbeat run, failure/recovery, run state machine |

## 2. `workflow-run`

기존 path:

```text
definition
→ run + claimWorkflowRunSlot(atomic slot)
→ step-runs dispatch
→ agent in-run contract(workflow-agent-api)
→ complete/retry + syncWorkflowRunState(downstream materialize)
→ reconciler(stuck/orphan/deadlock)
```

| 구분 | 원본 코드에서 확인할 항목 |
|---|---|
| Actor/trigger | 사용자, mission, schedule, event 중 workflow run을 만드는 실제 주체 |
| Entry point | definition 실행 route/service/job와 run 생성 transaction |
| Preconditions | definition 활성 상태, DAG 유효성, ownership, concurrency/slot 제한 |
| Decisions | runnable step 계산, 조건 edge, join, retry 가능 여부, terminal 판정 |
| State | workflow run과 step run의 전체 state machine 및 합법 전이 |
| Atomicity | slot claim, step claim, downstream materialization의 transaction/CAS 경계 |
| Async boundary | agent dispatch와 completion callback/event의 상관관계·idempotency key |
| Failure | step failure, agent loss, stuck/orphan, deadlock, reconciliation conflict |
| Retry | step/run retry count, backoff, 재실행 시 입력·artifact 보존 정책 |
| Compensation | 이미 완료한 step을 되돌리는지, 되돌리지 않는다면 partial outcome을 어떻게 표시하는지 |
| Outcomes | completed, failed, cancelled, partial, stuck-recovered 등 관측 가능한 종료 |
| 권장 child diagrams | run creation/claim, DAG step execution, conditional/join, reconciliation, run/step states |

## 3. `mission-supervision`

기존 path:

```text
mission issue
→ supervision 진단
→ owner-action decision 또는 grace default
→ retry/complete/recovery
→ plan-QA verdict
```

| 구분 | 원본 코드에서 확인할 항목 |
|---|---|
| Actor/trigger | mission owner, supervisor, scheduler, QA agent, user intervention의 역할 |
| Entry point | mission issue event, periodic monitor, owner action, QA verdict callback |
| Preconditions | mission status, current owner, active workflow/run, grace period, governance requirement |
| Decisions | 완료처럼 보이는 실패 탐지, retry/replan/recovery/complete 결정 기준 |
| State | mission, issue, owner action, plan QA, quality verdict, recovery attempt 전이 |
| Evidence | 어떤 work product·test·artifact·comment가 판단 입력이 되는지 |
| Timeout/grace | grace default가 발동하는 시간·상태·중복 방지 조건 |
| Retry/replan | retry와 replan의 차이, 새 subagent 생성 여부, 최대 반복·중단 조건 |
| Failure | evaluator 통과 오류, owner 부재, workflow 정지, stale evidence, conflicting verdict |
| Compensation | 잘못 완료 처리된 mission을 reopen/requeue/recover할 때 어떤 상태를 되돌리는지 |
| Outcomes | approved complete, rejected/rework, retry queued, recovery opened, escalation |
| 권장 child diagrams | supervision decision loop, plan-QA, content/final QA, recovery/replan, mission state machine |

## 4. `cross-company-delegation`

기존 path:

```text
mission delegation
→ SRB signed webhook
→ target-company mission 생성
→ handoff issue(blocked)
→ 산출물 copy-back
```

| 구분 | 원본 코드에서 확인할 항목 |
|---|---|
| Actor/trigger | source company, target company, delegating agent/user, relay worker |
| Entry point | delegation command/route, outbound dispatch, inbound webhook |
| Preconditions | company link, permission, direction, remote/local routing, secret availability |
| Decisions | local vs remote, signature/nonce/time validity, duplicate delivery, target acceptance |
| State | delegation, delivery log, mirrored issue, target mission, handoff, copy-back 상태 전이 |
| Security | signature 검증 순서, key rotation overlap, replay protection, transaction boundary |
| Async boundary | outbound delivery, retry worker, target processing, result copy-back correlation |
| Retry | delivery backoff, max attempt, dead status, duplicate/idempotent handling |
| Failure | authentication, nonce conflict, target create failure, partial copy-back, pair-sync conflict |
| Compensation | target mission이 만들어진 뒤 source handoff 실패 시 정리·재연결 정책 |
| Outcomes | delegated/accepted, rejected, retrying, dead delivery, completed/copy-back complete |
| 권장 child diagrams | outbound delegation, inbound authenticated webhook, delivery retry, issue/mission pairing, copy-back |

## 공통 acceptance gate

각 stream은 다음 조건을 모두 충족해야 승인한다.

- actor와 trigger가 코드 근거를 가진다.
- entry point가 route/event/job/symbol로 식별된다.
- 모든 decision에 두 개 이상의 조건 라벨 branch가 있다.
- state-changing step은 before/after state를 가진다.
- 외부·비동기 호출은 timeout, duplicate, retry, idempotency를 검토한다.
- 성공뿐 아니라 거절·실패·취소·부분 성공·복구 결과가 terminal outcome으로 연결된다.
- child diagram이 생성되고 master map에 합성된다.
- 모든 node가 flow/domain/entity/state/rule/code evidence note로 연결된다.
- SVG/PNG preview를 실제로 열어 시작점, happy path, failure path, terminal outcome을 확인한다.
