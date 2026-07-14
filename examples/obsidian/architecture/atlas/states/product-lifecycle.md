---
type: "state-machine"
id: "product-lifecycle"
confidence: "VERIFIED"
entity: "product"
initial_state: "DRAFT"
---
# Product lifecycle

- Entity: [[../entities/product|Product]]
- Initial state: `DRAFT`

## States

| State | Terminal | Meaning |
|---|---:|---|
| `DRAFT` | no | Not visible or orderable |
| `ACTIVE` | no | Potentially orderable inside sale window |
| `PAUSED` | no | Temporarily not orderable |
| `DISCONTINUED` | yes | No longer orderable |

## Transitions

| From | To | Trigger | Guard | Effect | Stream steps |
|---|---|---|---|---|---|
| `DRAFT` | `ACTIVE` | admin publishes | required product data present | catalog exposes product |  |
| `ACTIVE` | `PAUSED` | admin pauses | none | ordering rejects product | `place-order.check-product` |

## Diagram

![[../excalidraw/state-product-order-eligibility.excalidraw]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#catalog/product-state`
