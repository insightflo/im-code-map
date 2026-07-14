---
type: "business-rule"
id: "rule-stock-available"
confidence: "VERIFIED"
scope: "inventory reservation"
streams:
  - "browse-orderable-products"
  - "member-place-order"
---
# Requested stock must be available

- **Scope:** inventory reservation
- **Condition:** `availableQty >= requestedQty`
- **Outcome:** reserve atomically; otherwise OUT_OF_STOCK

## Used by streams

- [[../flows/browse-orderable-products|Browse products with orderability]]
- [[../flows/member-place-order|Verified member places an order]]

## Governs entities

- [[../entities/inventory-item|Inventory item]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#inventory/reservation`
