---
type: "domain"
id: "catalog"
confidence: "VERIFIED"
domain_type: "business"
streams:
  - "browse-orderable-products"
  - "member-place-order"
---
# Catalog

Publish products and determine product sale eligibility.

## Responsibilities

- product publication
- sale window checks
- price lookup

## Business streams using this domain

- [[../flows/browse-orderable-products|Browse products with orderability]]
- [[../flows/member-place-order|Verified member places an order]]

## Owned entities and state

- [[../entities/product|Product]]
- [[../states/product-lifecycle|Product lifecycle]]

## Contracts

| Direction | Kind | Contract | Streams |
|---|---|---|---|
| ← [[../domains/ordering|Ordering]] | `query` / `sync` | `GetOrderability(productId, now)` | [[../flows/member-place-order|member-place-order]] |

## Implementation locations

- [[../codebases/commerce-app|Commerce application]]: `src/catalog`

## Visuals

- [[../visual-index|Visual index]]
- [[../excalidraw/domain-commerce-overview.excalidraw|Domain overview]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#catalog/product-policy`
