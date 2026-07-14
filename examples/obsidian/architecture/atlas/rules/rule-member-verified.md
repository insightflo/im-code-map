---
type: "business-rule"
id: "rule-member-verified"
confidence: "VERIFIED"
scope: "order placement"
streams:
  - "member-place-order"
---
# Verified member required

- **Scope:** order placement
- **Condition:** `member.role contains MEMBER and member.status == VERIFIED`
- **Outcome:** allow order request; otherwise reject before order creation

## Used by streams

- [[../flows/member-place-order|Verified member places an order]]

## Governs entities

- [[../entities/member|Member]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#auth/order-policy`
