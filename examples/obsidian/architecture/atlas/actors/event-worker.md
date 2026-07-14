---
type: "actor"
id: "event-worker"
confidence: "VERIFIED"
actor_type: "system"
roles:
  - "EVENT_CONSUMER"
---
# Order event worker

## Entry points

- `order.placed`

## Permissions

- send confirmation
- start fulfillment

## Participating streams

- [[../flows/member-place-order|Verified member places an order]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#workers/order-events`
