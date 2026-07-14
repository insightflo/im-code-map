# Visual Architecture Index

Generated at: {{generated_at}}  
Workspace: `{{workspace_id}}`

## 가장 먼저 볼 그림

- Master infinite-canvas map: [[{{master_excalidraw}}]]
- Primary business stream: [[{{primary_stream_excalidraw}}]]
- State and eligibility: [[{{primary_state_excalidraw}}]]
- Workspace Canvas: [[{{workspace_canvas}}]]
- Machine models: [[{{map_model}}]] · [[{{visual_model}}]]

## Business stream diagrams

| Stream | Actor / trigger | Entry point | Success and failure outcomes | Child diagram | Confidence |
|---|---|---|---|---|---|
| {{stream_name}} | {{actor_trigger}} | `{{entry_point}}` | {{outcomes}} | [[{{stream_excalidraw}}]] | {{confidence}} |

## State and eligibility diagrams

| Entity/state machine | What it controls | Diagram | Related streams | Confidence |
|---|---|---|---|---|
| {{state_machine}} | {{controlled_behavior}} | [[{{state_excalidraw}}]] | {{stream_links}} | {{confidence}} |

## Domain responsibility diagrams

| Domain/context | Ownership and contracts | Diagram | Participating streams | Confidence |
|---|---|---|---|---|
| {{domain_name}} | {{responsibility}} | [[{{domain_excalidraw}}]] | {{stream_links}} | {{confidence}} |

## Change-impact diagrams

| Change | Affected stream/state | Diagram | Status |
|---|---|---|---|
| {{change_id}} | {{affected_behavior}} | [[{{change_excalidraw}}]] | {{status}} |

## Visual QA

- Last review: [[{{visual_review_report}}]]
- Unresolved visual or evidence risks: {{uncertainty}}
