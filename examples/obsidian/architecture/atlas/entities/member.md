---
type: "entity"
id: "member"
confidence: "VERIFIED"
domain: "identity-access"
states:
  - "GUEST"
  - "REGISTERED"
  - "VERIFIED"
  - "SUSPENDED"
---
# Member

- Owner: [[../domains/identity-access|Identity & Access]]

## Lifecycle states

- `GUEST`
- `REGISTERED`
- `VERIFIED`
- `SUSPENDED`

## Eligibility rules

- [[../rules/rule-member-verified|Verified member required]]

## Related streams

- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#auth/member`
