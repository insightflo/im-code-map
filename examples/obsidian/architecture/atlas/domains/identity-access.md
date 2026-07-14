---
type: "domain"
id: "identity-access"
confidence: "VERIFIED"
domain_type: "cross-cutting"
streams:
  - "browse-orderable-products"
  - "member-place-order"
  - "cancel-order"
---
# Identity & Access

Resolve member type, verification, and permissions.

## Responsibilities

- authenticate member
- authorize order action

## Business streams using this domain

- [[../flows/browse-orderable-products|Browse products with orderability]]
- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Owned entities and state

- [[../entities/member|Member]]

## Contracts

- No typed cross-domain contract recorded.

## Implementation locations

- [[../codebases/commerce-app|Commerce application]]: `src/auth`, `src/policies/order-policy.ts`

## Visuals

- [[../visual-index|Visual index]]
- [[../excalidraw/domain-commerce-overview.excalidraw|Domain overview]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#auth/order-policy`
