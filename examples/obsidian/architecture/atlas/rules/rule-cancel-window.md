---
type: "business-rule"
id: "rule-cancel-window"
confidence: "PARTIAL"
scope: "order cancellation"
streams:
  - "cancel-order"
---
# Only cancellable orders can be cancelled

- **Scope:** order cancellation
- **Condition:** `order.status in [RESERVED, PAID] and fulfillment not started`
- **Outcome:** cancel and compensate; otherwise CANCELLATION_REJECTED

## Used by streams

- [[../flows/cancel-order|Cancel an eligible order]]

## Governs entities

- None evidenced.

## Evidence

- `examples/demo-commerce/source-snapshot.md#orders/cancel-policy`
