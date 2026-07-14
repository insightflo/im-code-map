---
type: "architecture-start"
id: "demo-commerce"
confidence: "PARTIAL"
schema_version: "5.0.0"
---
# demo-commerce architecture

> Read the business stream first. Domain ownership explains *where* work lives; it does not explain *what happens*.

## Primary reading path

1. [[flows/member-place-order|Verified member places an order]]
2. [[visual-index|Visual index]]
3. [[workspace-stream-map.canvas|Workspace stream canvas]]
4. [[excalidraw/stream-member-place-order.excalidraw|Primary Excalidraw stream]]

## Business streams

- [[flows/browse-orderable-products|Browse products with orderability]] · `VERIFIED`
- [[flows/member-place-order|Verified member places an order]] · `PARTIAL`
- [[flows/cancel-order|Cancel an eligible order]] · `PARTIAL`

## State and eligibility

- [[states/product-lifecycle|Product lifecycle]]
- [[states/order-lifecycle|Order lifecycle]]
- [[states/payment-lifecycle|Payment lifecycle]]

## Domain context

- [[domains/identity-access|Identity & Access]]
- [[domains/catalog|Catalog]]
- [[domains/inventory|Inventory]]
- [[domains/ordering|Ordering]]
- [[domains/payment|Payment]]

## Machine-readable sources

- `map-model.json`
- `visual-model.json`
