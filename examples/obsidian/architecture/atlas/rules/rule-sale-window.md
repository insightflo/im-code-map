---
type: "business-rule"
id: "rule-sale-window"
confidence: "VERIFIED"
scope: "order eligibility"
streams:
  - "browse-orderable-products"
  - "member-place-order"
---
# Sale window must be open

- **Scope:** order eligibility
- **Condition:** `saleStartsAt <= now < saleEndsAt`
- **Outcome:** continue; otherwise SALE_WINDOW_CLOSED

## Used by streams

- [[../flows/browse-orderable-products|Browse products with orderability]]
- [[../flows/member-place-order|Verified member places an order]]

## Governs entities

- [[../entities/product|Product]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#catalog/product-policy`
