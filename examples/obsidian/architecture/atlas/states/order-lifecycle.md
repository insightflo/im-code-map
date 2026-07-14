---
type: "state-machine"
id: "order-lifecycle"
confidence: "VERIFIED"
entity: "order"
initial_state: "PENDING"
---
# Order lifecycle

- Entity: [[../entities/order|Order]]
- Initial state: `PENDING`

## States

| State | Terminal | Meaning |
|---|---:|---|
| `PENDING` | no | Order exists, stock not yet guaranteed |
| `RESERVED` | no | Stock reserved, payment pending |
| `PAID` | yes | Payment authorized |
| `FAILED` | yes | Order cannot complete |
| `CANCELLED` | yes | Order cancelled and resources released |

## Transitions

| From | To | Trigger | Guard | Effect | Stream steps |
|---|---|---|---|---|---|
| `PENDING` | `RESERVED` | stock reservation succeeds | availableQty >= requestedQty | persist reservation | `place-order.reserve-stock`, `place-order.mark-reserved` |
| `RESERVED` | `PAID` | payment authorized | payment result AUTHORIZED | mark order paid and emit event | `place-order.mark-paid` |
| `PENDING` | `FAILED` | eligibility or stock failure | validation fails | record failure reason | `place-order.end-rejected` |

## Diagram

![[../excalidraw/state-product-order-eligibility.excalidraw]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#orders/state-machine`
