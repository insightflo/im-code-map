---
type: "state-machine"
id: "payment-lifecycle"
confidence: "PARTIAL"
entity: "payment"
initial_state: "REQUESTED"
---
# Payment lifecycle

- Entity: [[../entities/payment|Payment]]
- Initial state: `REQUESTED`

## States

| State | Terminal | Meaning |
|---|---:|---|
| `REQUESTED` | no | Charge requested |
| `AUTHORIZED` | yes | Charge accepted |
| `DECLINED` | yes | Charge rejected |
| `REFUNDED` | yes | Authorized payment reversed |

## Transitions

| From | To | Trigger | Guard | Effect | Stream steps |
|---|---|---|---|---|---|
| `REQUESTED` | `AUTHORIZED` | gateway authorizes | gateway response authorized | store authorization id | `place-order.check-payment` |
| `REQUESTED` | `DECLINED` | gateway declines | decline response | store decline reason | `place-order.payment-failed` |

## Diagram

![[../excalidraw/state-product-order-eligibility.excalidraw]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#payments/state`
