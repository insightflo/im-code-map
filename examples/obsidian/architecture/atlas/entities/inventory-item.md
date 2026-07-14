---
type: "entity"
id: "inventory-item"
confidence: "VERIFIED"
domain: "inventory"
states:
  - "AVAILABLE"
  - "LOW"
  - "OUT_OF_STOCK"
---
# Inventory item

- Owner: [[../domains/inventory|Inventory]]

## Lifecycle states

- `AVAILABLE`
- `LOW`
- `OUT_OF_STOCK`

## Eligibility rules

- [[../rules/rule-stock-available|Requested stock must be available]]

## Related streams

- [[../flows/browse-orderable-products|Browse products with orderability]]
- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#inventory/item`
