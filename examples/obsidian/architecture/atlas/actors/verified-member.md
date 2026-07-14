---
type: "actor"
id: "verified-member"
confidence: "VERIFIED"
actor_type: "human"
roles:
  - "MEMBER"
  - "VERIFIED"
---
# Verified member

## Entry points

- `POST /orders`

## Permissions

- place orders
- cancel own cancellable orders

## Participating streams

- [[../flows/member-place-order|Verified member places an order]]
- [[../flows/cancel-order|Cancel an eligible order]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#auth/order-policy`
