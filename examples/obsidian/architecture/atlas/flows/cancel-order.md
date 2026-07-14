---
type: "business-stream"
id: "cancel-order"
confidence: "PARTIAL"
actors:
  - "verified-member"
  - "commerce-api"
  - "payment-gateway"
domains:
  - "identity-access"
  - "ordering"
  - "inventory"
  - "payment"
---
# Cancel an eligible order

Trace cancellation policy, refund/release compensation, and terminal order state.

## Trigger

- Kind: `user-intent`
- Source: `verified-member`
- Event: **cancel order**
- Entry point: `POST /orders/{id}/cancel`

## Actors and systems

- [[../actors/verified-member|Verified member]]
- [[../actors/commerce-api|Commerce API]]
- [[../actors/payment-gateway|Payment gateway]]

## Preconditions

- **Member owns the order or has admin permission.** Rules: [[../rules/rule-cancel-window|Only cancellable orders can be cancelled]]. Failure: `cancellation rejected`.

## Stream

| # | Actor/System | Domain | Kind | Processing | Reads / writes | State change | Rules | Confidence |
|---:|---|---|---|---|---|---|---|---|
| 0 | [[../actors/verified-member|Verified member]] | [[../domains/ordering|Ordering]] | `start` | <a id="start"></a>**Request cancellation**: Submit own order id. |  |  |  | `VERIFIED` |
| 1 | [[../actors/commerce-api|Commerce API]] | [[../domains/ordering|Ordering]] | `decision` | <a id="check"></a>**Is cancellation allowed?**: Check ownership, status, and fulfillment state. |  |  | [[../rules/rule-cancel-window|Only cancellable orders can be cancelled]] | `VERIFIED` |
| 2 | [[../actors/commerce-api|Commerce API]] | [[../domains/payment|Payment]] | `compensation` | <a id="compensate"></a>**Refund and release**: Refund payment when present and release stock. |  |  |  | `PARTIAL` |
| 3 | [[../actors/commerce-api|Commerce API]] | [[../domains/ordering|Ordering]] | `state-change` | <a id="mark"></a>**Mark order cancelled**: Persist CANCELLED. |  | `order PAID→CANCELLED` |  | `PARTIAL` |
| 4 | [[../actors/verified-member|Verified member]] | [[../domains/ordering|Ordering]] | `end` | <a id="success"></a>**Return cancelled**: Show cancellation confirmation. |  |  |  | `PARTIAL` |
| 5 | [[../actors/commerce-api|Commerce API]] | [[../domains/ordering|Ordering]] | `end` | <a id="rejected"></a>**Reject cancellation**: Return policy reason without state change. |  |  |  | `PARTIAL` |

## Branches and transitions

| From | Condition / reason | To | Type |
|---|---|---|---|
| `cancel.start` Request cancellation | **request** · order loaded | `cancel.check` Is cancellation allowed? | `happy-path` |
| `cancel.check` Is cancellation allowed? | **allowed** · own order and fulfillment not started | `cancel.compensate` Refund and release | `conditional` |
| `cancel.check` Is cancellation allowed? | **not allowed** · policy failed | `cancel.rejected` Reject cancellation | `conditional` |
| `cancel.compensate` Refund and release | **resources restored** · refund/release succeeded | `cancel.mark` Mark order cancelled | `compensation` |
| `cancel.mark` Mark order cancelled | **cancelled** · state persisted | `cancel.success` Return cancelled | `happy-path` |

## Terminal outcomes

| Outcome | Type | Terminal step | Observable result |
|---|---|---|---|
| **Order cancelled and resources restored** | `success` | `cancel.success` | CANCELLED order |
| **Policy rejected cancellation** | `rejected` | `cancel.rejected` | No state change |

## Errors, retries, and compensation

- No explicit error path modeled. Verify this is intentional.
- **Compensation `cancel-refund-release`:** when approved cancellation, refund authorized payment and release reserved stock; restores member funds and inventory availability.

## State changes

- `order RESERVED/PAID→CANCELLED`
- `payment AUTHORIZED→REFUNDED when paid`

## Domains touched

- [[../domains/identity-access|Identity & Access]]
- [[../domains/ordering|Ordering]]
- [[../domains/inventory|Inventory]]
- [[../domains/payment|Payment]]

## Visuals

- [[../excalidraw/stream-cancel-order.excalidraw|stream-cancel-order.excalidraw]]

![[../excalidraw/stream-cancel-order.excalidraw]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#orders/cancel`
