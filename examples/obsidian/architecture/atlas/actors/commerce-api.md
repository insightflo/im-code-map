---
type: "actor"
id: "commerce-api"
confidence: "VERIFIED"
actor_type: "system"
roles:
  - "ORCHESTRATOR"
---
# Commerce API

## Entry points

- `POST /orders`

## Permissions

- query catalog
- create orders
- reserve inventory
- request payment

## Participating streams

- [[../flows/browse-orderable-products|Browse products with orderability]]
- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#services/order-service`
