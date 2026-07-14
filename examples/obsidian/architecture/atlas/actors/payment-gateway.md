---
type: "actor"
id: "payment-gateway"
confidence: "PARTIAL"
actor_type: "external"
roles:
  - "PAYMENT_PROVIDER"
---
# Payment gateway

## Entry points

- `POST /charges`

## Permissions

- authorize or decline charge

## Participating streams

- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#adapters/payment-gateway`
