---
type: "domain"
id: "payment"
confidence: "PARTIAL"
domain_type: "supporting"
streams:
  - "member-place-order"
  - "cancel-order"
---
# Payment

Authorize payment and record results.

## Responsibilities

- charge request
- result recording
- refund

## Business streams using this domain

- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Owned entities and state

- [[../entities/payment|Payment]]
- [[../states/payment-lifecycle|Payment lifecycle]]

## Contracts

| Direction | Kind | Contract | Streams |
|---|---|---|---|
| ← [[../domains/ordering|Ordering]] | `command` / `sync` | `Authorize(orderId, amount, token)` | [[../flows/member-place-order|member-place-order]] |
| ← [[../domains/ordering|Ordering]] | `event` / `async` | `order.placed` | [[../flows/member-place-order|member-place-order]] |

## Implementation locations

- [[../codebases/commerce-app|Commerce application]]: `src/payments`

## Visuals

- [[../visual-index|Visual index]]
- [[../excalidraw/domain-commerce-overview.excalidraw|Domain overview]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#payments/charge`
