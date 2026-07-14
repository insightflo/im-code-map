---
type: "entity"
id: "order"
confidence: "VERIFIED"
domain: "ordering"
states:
  - "PENDING"
  - "RESERVED"
  - "PAID"
  - "FAILED"
  - "CANCELLED"
---
# Order

- Owner: [[../domains/ordering|Ordering]]
- State machine: [[../states/order-lifecycle|Order lifecycle]]

## Lifecycle states

- `PENDING`
- `RESERVED`
- `PAID`
- `FAILED`
- `CANCELLED`

## Eligibility rules

- None evidenced.

## Related streams

- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#orders/state-machine`
