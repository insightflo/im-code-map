---
type: "entity"
id: "payment"
confidence: "PARTIAL"
domain: "payment"
states:
  - "REQUESTED"
  - "AUTHORIZED"
  - "DECLINED"
  - "REFUNDED"
---
# Payment

- Owner: [[../domains/payment|Payment]]
- State machine: [[../states/payment-lifecycle|Payment lifecycle]]

## Lifecycle states

- `REQUESTED`
- `AUTHORIZED`
- `DECLINED`
- `REFUNDED`

## Eligibility rules

- None evidenced.

## Related streams

- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#payments/payment`
