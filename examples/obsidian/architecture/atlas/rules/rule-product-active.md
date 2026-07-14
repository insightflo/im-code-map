---
type: "business-rule"
id: "rule-product-active"
confidence: "VERIFIED"
scope: "order eligibility"
streams:
  - "browse-orderable-products"
  - "member-place-order"
---
# Product must be active

- **Scope:** order eligibility
- **Condition:** `product.status == ACTIVE`
- **Outcome:** continue; otherwise PRODUCT_NOT_ORDERABLE

## Used by streams

- [[../flows/browse-orderable-products|Browse products with orderability]]
- [[../flows/member-place-order|Verified member places an order]]

## Governs entities

- [[../entities/product|Product]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#catalog/product-policy`
