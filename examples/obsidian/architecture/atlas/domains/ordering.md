---
type: "domain"
id: "ordering"
confidence: "VERIFIED"
domain_type: "business"
streams:
  - "member-place-order"
  - "cancel-order"
---
# Ordering

Create and evolve orders through their lifecycle.

## Responsibilities

- order creation
- state transition
- cancellation

## Business streams using this domain

- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Owned entities and state

- [[../entities/order|Order]]
- [[../states/order-lifecycle|Order lifecycle]]

## Contracts

| Direction | Kind | Contract | Streams |
|---|---|---|---|
| → [[../domains/catalog|Catalog]] | `query` / `sync` | `GetOrderability(productId, now)` | [[../flows/member-place-order|member-place-order]] |
| → [[../domains/inventory|Inventory]] | `command` / `sync` | `Reserve(productId, qty, orderId)` | [[../flows/member-place-order|member-place-order]] |
| → [[../domains/payment|Payment]] | `command` / `sync` | `Authorize(orderId, amount, token)` | [[../flows/member-place-order|member-place-order]] |
| → [[../domains/payment|Payment]] | `event` / `async` | `order.placed` | [[../flows/member-place-order|member-place-order]] |

## Implementation locations

- [[../codebases/commerce-app|Commerce application]]: `src/orders`

## Visuals

- [[../visual-index|Visual index]]
- [[../excalidraw/domain-commerce-overview.excalidraw|Domain overview]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#orders/state-machine`
