---
type: "business-stream"
id: "member-place-order"
confidence: "PARTIAL"
actors:
  - "verified-member"
  - "commerce-api"
  - "payment-gateway"
  - "event-worker"
domains:
  - "identity-access"
  - "catalog"
  - "inventory"
  - "ordering"
  - "payment"
---
# Verified member places an order

Trace member eligibility, product eligibility, stock reservation, payment, state transitions, and compensation from request to terminal result.

## Trigger

- Kind: `user-intent`
- Source: `verified-member`
- Event: **place order**
- Entry point: `POST /orders`

## Actors and systems

- [[../actors/verified-member|Verified member]]
- [[../actors/commerce-api|Commerce API]]
- [[../actors/payment-gateway|Payment gateway]]
- [[../actors/event-worker|Order event worker]]

## Preconditions

- **Request resolves to a member identity.** Rules: [[../rules/rule-member-verified|Verified member required]]. Failure: `ineligible`.
- **productId, positive quantity, and payment token are present.** Rules: none. Failure: `validation error`.

## Stream

| # | Actor/System | Domain | Kind | Processing | Reads / writes | State change | Rules | Confidence |
|---:|---|---|---|---|---|---|---|---|
| 0 | [[../actors/verified-member|Verified member]] | [[../domains/ordering|Ordering]] | `start` | <a id="start"></a>**Member starts checkout**: Submit product, quantity, and payment token. |  |  |  | `VERIFIED` |
| 1 | [[../actors/commerce-api|Commerce API]] | [[../domains/identity-access|Identity & Access]] | `decision` | <a id="check-member"></a>**Check member eligibility**: Resolve member type, verification, and suspension status. | R: `member.status`, `member.roles` |  | [[../rules/rule-member-verified|Verified member required]] | `VERIFIED` |
| 2 | [[../actors/commerce-api|Commerce API]] | [[../domains/catalog|Catalog]] | `data-read` | <a id="load-product"></a>**Load product and price**: Read product status, sale window, and current price. | R: `product.status`, `saleStartsAt`, `saleEndsAt`, `price` |  |  | `VERIFIED` |
| 3 | [[../actors/commerce-api|Commerce API]] | [[../domains/catalog|Catalog]] | `decision` | <a id="check-product"></a>**Is product orderable?**: Evaluate active state and sale window. |  |  | [[../rules/rule-product-active|Product must be active]], [[../rules/rule-sale-window|Sale window must be open]] | `VERIFIED` |
| 4 | [[../actors/commerce-api|Commerce API]] | [[../domains/ordering|Ordering]] | `state-change` | <a id="create-pending"></a>**Create pending order**: Create order with immutable product/price snapshot. | W: `order` | `order NONE→PENDING` |  | `VERIFIED` |
| 5 | [[../actors/commerce-api|Commerce API]] | [[../domains/inventory|Inventory]] | `process` | <a id="reserve-stock"></a>**Reserve stock atomically**: Reserve requested quantity for order. | R: `inventory.availableQty`; W: `inventory.reservedQty` |  | [[../rules/rule-stock-available|Requested stock must be available]] | `VERIFIED` |
| 6 | [[../actors/commerce-api|Commerce API]] | [[../domains/inventory|Inventory]] | `decision` | <a id="check-reservation"></a>**Was stock reserved?**: Branch on atomic reservation result. |  |  |  | `VERIFIED` |
| 7 | [[../actors/commerce-api|Commerce API]] | [[../domains/ordering|Ordering]] | `state-change` | <a id="mark-reserved"></a>**Mark order reserved**: Persist successful reservation on the order. | W: `order.status`, `order.reservationId` | `order PENDING→RESERVED` |  | `VERIFIED` |
| 8 | [[../actors/commerce-api|Commerce API]] | [[../domains/payment|Payment]] | `external-call` | <a id="request-payment"></a>**Request payment authorization**: Send amount and payment token to gateway. | W: `payment` | `payment NONE→REQUESTED` |  | `PARTIAL` |
| 9 | [[../actors/commerce-api|Commerce API]] | [[../domains/payment|Payment]] | `decision` | <a id="check-payment"></a>**Was payment authorized?**: Branch on gateway result. |  |  |  | `PARTIAL` |
| 10 | [[../actors/commerce-api|Commerce API]] | [[../domains/ordering|Ordering]] | `state-change` | <a id="mark-paid"></a>**Mark order paid**: Record authorization and complete order. | W: `order.status`, `order.paymentId` | `order RESERVED→PAID`; `payment REQUESTED→AUTHORIZED` |  | `VERIFIED` |
| 11 | [[../actors/commerce-api|Commerce API]] | [[../domains/ordering|Ordering]] | `event` | <a id="emit-event"></a>**Publish order.placed**: Emit the completed-order event for downstream work. |  |  |  | `VERIFIED` |
| 12 | [[../actors/verified-member|Verified member]] | [[../domains/ordering|Ordering]] | `end` | <a id="confirm"></a>**Show confirmation**: Return order number and paid status. |  |  |  | `VERIFIED` |
| 20 | [[../actors/commerce-api|Commerce API]] | [[../domains/identity-access|Identity & Access]] | `end` | <a id="end-ineligible"></a>**Reject ineligible member**: Return MEMBER_NOT_ELIGIBLE without creating an order. |  |  |  | `VERIFIED` |
| 21 | [[../actors/commerce-api|Commerce API]] | [[../domains/catalog|Catalog]] | `end` | <a id="end-not-orderable"></a>**Reject unavailable product**: Return product-state or sale-window reason. |  |  |  | `VERIFIED` |
| 22 | [[../actors/commerce-api|Commerce API]] | [[../domains/ordering|Ordering]] | `error-handler` | <a id="stock-failed"></a>**Fail order for stock**: Mark pending order failed with OUT_OF_STOCK. | W: `order.status`, `order.failureReason` | `order PENDING→FAILED` |  | `VERIFIED` |
| 23 | [[../actors/commerce-api|Commerce API]] | [[../domains/inventory|Inventory]] | `end` | <a id="end-stock-failed"></a>**Return out-of-stock result**: Return OUT_OF_STOCK and no payment request. |  |  |  | `VERIFIED` |
| 24 | [[../actors/commerce-api|Commerce API]] | [[../domains/payment|Payment]] | `compensation` | <a id="payment-failed"></a>**Record decline and release stock**: Mark payment declined, fail order, and release reservation. | W: `payment.status`, `order.status`, `inventory.reservedQty` | `payment REQUESTED→DECLINED`; `order RESERVED→FAILED` |  | `PARTIAL` |
| 25 | [[../actors/commerce-api|Commerce API]] | [[../domains/payment|Payment]] | `end` | <a id="end-payment-failed"></a>**Return payment failure**: Return PAYMENT_DECLINED after compensation. |  |  |  | `VERIFIED` |

## Branches and transitions

| From | Condition / reason | To | Type |
|---|---|---|---|
| `place-order.start` Member starts checkout | **submit** · request received | `place-order.check-member` Check member eligibility | `happy-path` |
| `place-order.check-member` Check member eligibility | **eligible** · member is VERIFIED and not SUSPENDED | `place-order.load-product` Load product and price | `conditional` |
| `place-order.check-member` Check member eligibility | **not eligible** · guest, unverified, or suspended | `place-order.end-ineligible` Reject ineligible member | `conditional` |
| `place-order.load-product` Load product and price | **loaded** · product found | `place-order.check-product` Is product orderable? | `happy-path` |
| `place-order.check-product` Is product orderable? | **orderable** · status ACTIVE and sale window open | `place-order.create-pending` Create pending order | `conditional` |
| `place-order.check-product` Is product orderable? | **not orderable** · inactive or sale window closed | `place-order.end-not-orderable` Reject unavailable product | `conditional` |
| `place-order.create-pending` Create pending order | **pending order** · orderId created | `place-order.reserve-stock` Reserve stock atomically | `happy-path` |
| `place-order.reserve-stock` Reserve stock atomically | **reservation result** · atomic update returned | `place-order.check-reservation` Was stock reserved? | `happy-path` |
| `place-order.check-reservation` Was stock reserved? | **reserved** · availableQty >= requestedQty | `place-order.mark-reserved` Mark order reserved | `conditional` |
| `place-order.check-reservation` Was stock reserved? | **out of stock** · reservation rejected | `place-order.stock-failed` Fail order for stock | `error` |
| `place-order.stock-failed` Fail order for stock | **failed** · order marked FAILED | `place-order.end-stock-failed` Return out-of-stock result | `error` |
| `place-order.mark-reserved` Mark order reserved | **reserved** · order status RESERVED | `place-order.request-payment` Request payment authorization | `happy-path` |
| `place-order.request-payment` Request payment authorization | **gateway result** · response received | `place-order.check-payment` Was payment authorized? | `happy-path` |
| `place-order.check-payment` Was payment authorized? | **authorized** · gateway status AUTHORIZED | `place-order.mark-paid` Mark order paid | `conditional` |
| `place-order.check-payment` Was payment authorized? | **declined or timeout** · authorization not obtained | `place-order.payment-failed` Record decline and release stock | `error` |
| `place-order.payment-failed` Record decline and release stock | **released** · order failed and stock released | `place-order.end-payment-failed` Return payment failure | `compensation` |
| `place-order.mark-paid` Mark order paid | **paid** · order status PAID | `place-order.emit-event` Publish order.placed | `happy-path` |
| `place-order.emit-event` Publish order.placed | **published** · event accepted; response does not wait for worker | `place-order.confirm` Show confirmation | `async-event` |

## Terminal outcomes

| Outcome | Type | Terminal step | Observable result |
|---|---|---|---|
| **Order paid and event published** | `success` | `place-order.confirm` | HTTP 201 with PAID order number |
| **Member cannot place order** | `rejected` | `place-order.end-ineligible` | HTTP 403 MEMBER_NOT_ELIGIBLE |
| **Product state or sale window blocks order** | `rejected` | `place-order.end-not-orderable` | HTTP 409 with reason |
| **Stock reservation failed** | `failed` | `place-order.end-stock-failed` | HTTP 409 OUT_OF_STOCK and order FAILED |
| **Payment failed after stock reservation** | `failed` | `place-order.end-payment-failed` | HTTP 402/409 and reservation released |

## Errors, retries, and compensation

- `OUT_OF_STOCK` at `place-order.check-reservation` → handler `place-order.stock-failed` → outcome `stock-failed`. Retry: User may retry after quantity change or restock.
- `DECLINED_OR_TIMEOUT` at `place-order.check-payment` → handler `place-order.payment-failed` → outcome `payment-failed`. Retry: No automatic charge retry; user may submit a new payment attempt.
- **Compensation `release-on-payment-failure`:** when payment not authorized after reservation, release inventory reservation and fail order; restores inventory availability; no paid order remains.

## State changes

- `order NONE→PENDING→RESERVED→PAID`
- `payment NONE→REQUESTED→AUTHORIZED`
- `error: order PENDING/RESERVED→FAILED`
- `error: payment REQUESTED→DECLINED`

## Domains touched

- [[../domains/identity-access|Identity & Access]]
- [[../domains/catalog|Catalog]]
- [[../domains/inventory|Inventory]]
- [[../domains/ordering|Ordering]]
- [[../domains/payment|Payment]]

## Visuals

- [[../excalidraw/stream-member-place-order.excalidraw|stream-member-place-order.excalidraw]]
- [[../excalidraw/state-product-order-eligibility.excalidraw|state-product-order-eligibility.excalidraw]]

![[../excalidraw/stream-member-place-order.excalidraw]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#services/order-service`
