---
type: "entity"
id: "product"
confidence: "VERIFIED"
domain: "catalog"
states:
  - "DRAFT"
  - "ACTIVE"
  - "PAUSED"
  - "DISCONTINUED"
---
# Product

- Owner: [[../domains/catalog|Catalog]]
- State machine: [[../states/product-lifecycle|Product lifecycle]]

## Lifecycle states

- `DRAFT`
- `ACTIVE`
- `PAUSED`
- `DISCONTINUED`

## Eligibility rules

- [[../rules/rule-product-active|Product must be active]]
- [[../rules/rule-sale-window|Sale window must be open]]

## Related streams

- [[../flows/browse-orderable-products|Browse products with orderability]]
- [[../flows/member-place-order|Verified member places an order]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#catalog/product`
