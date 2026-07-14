---
type: "business-stream"
id: "browse-orderable-products"
confidence: "VERIFIED"
actors:
  - "guest"
  - "commerce-api"
domains:
  - "catalog"
  - "inventory"
---
# Browse products with orderability

Explain why each visible product can or cannot be ordered.

## Trigger

- Kind: `user-intent`
- Source: `guest`
- Event: **open catalog**
- Entry point: `GET /products`

## Actors and systems

- [[../actors/guest|Guest shopper]]
- [[../actors/commerce-api|Commerce API]]

## Preconditions

- No explicit preconditions beyond request validity.

## Stream

| # | Actor/System | Domain | Kind | Processing | Reads / writes | State change | Rules | Confidence |
|---:|---|---|---|---|---|---|---|---|
| 0 | [[../actors/guest|Guest shopper]] | [[../domains/catalog|Catalog]] | `start` | <a id="start"></a>**Open catalog**: Request visible products. |  |  |  | `VERIFIED` |
| 1 | [[../actors/commerce-api|Commerce API]] | [[../domains/catalog|Catalog]] | `process` | <a id="filter"></a>**Filter orderable products**: Return products that are active and inside sale window. |  |  | [[../rules/rule-product-active|Product must be active]], [[../rules/rule-sale-window|Sale window must be open]] | `VERIFIED` |
| 2 | [[../actors/commerce-api|Commerce API]] | [[../domains/inventory|Inventory]] | `data-read` | <a id="add-stock"></a>**Attach availability**: Read whether at least one unit is available. |  |  | [[../rules/rule-stock-available|Requested stock must be available]] | `VERIFIED` |
| 3 | [[../actors/guest|Guest shopper]] | [[../domains/catalog|Catalog]] | `end` | <a id="end"></a>**Show orderability**: Show product plus orderable reason. |  |  |  | `VERIFIED` |

## Branches and transitions

| From | Condition / reason | To | Type |
|---|---|---|---|
| `browse.start` Open catalog | **request** · catalog opened | `browse.filter` Filter orderable products | `happy-path` |
| `browse.filter` Filter orderable products | **eligible catalog items** · product policy passed | `browse.add-stock` Attach availability | `happy-path` |
| `browse.add-stock` Attach availability | **availability attached** · stock read completed | `browse.end` Show orderability | `happy-path` |

## Terminal outcomes

| Outcome | Type | Terminal step | Observable result |
|---|---|---|---|
| **Catalog displayed** | `success` | `browse.end` | Each item has price and orderability reason |

## Errors, retries, and compensation

- No explicit error path modeled. Verify this is intentional.

## State changes

- None evidenced.

## Domains touched

- [[../domains/catalog|Catalog]]
- [[../domains/inventory|Inventory]]

## Visuals

- [[../excalidraw/stream-browse-orderable-products.excalidraw|stream-browse-orderable-products.excalidraw]]

![[../excalidraw/stream-browse-orderable-products.excalidraw]]

## Evidence

- `examples/demo-commerce/source-snapshot.md#routes/catalog`
