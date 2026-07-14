---
type: "domain"
id: "inventory"
confidence: "VERIFIED"
domain_type: "business"
streams:
  - "browse-orderable-products"
  - "member-place-order"
  - "cancel-order"
---
# Inventory

Expose availability and reserve or release stock.

## Responsibilities

- availability lookup
- atomic reservation
- reservation release

## Business streams using this domain

- [[../flows/browse-orderable-products|Browse products with orderability]]
- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Owned entities and state

- [[../entities/inventory-item|Inventory item]]

## Contracts

| Direction | Kind | Contract | Streams |
|---|---|---|---|
| ← [[../domains/ordering|Ordering]] | `command` / `sync` | `Reserve(productId, qty, orderId)` | [[../flows/member-place-order|member-place-order]] |

## Implementation locations

- [[../codebases/commerce-app|Commerce application]]: `src/inventory`

## Visuals

- [[../visual-index|Visual index]]
- [[../excalidraw/domain-commerce-overview.excalidraw|Domain overview]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#inventory/reservation`
