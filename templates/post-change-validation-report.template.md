# After Change Validation

Generated at: {{generated_at}}

## 먼저 볼 그림

- After impact diagram: `{{after_change_excalidraw}}`
- Updated domain overview: `{{domain_overview_excalidraw}}`
- Updated business stream: `{{feature_flow_excalidraw}}`

## 실제 변경 파일

- {{changed_file}}

## 변경된 도메인

- {{changed_domain}}

## 변경된 codebase

- {{changed_codebase}}

## 구조 변경

- 추가된 노드: {{added_nodes}}
- 제거된 노드: {{removed_nodes}}
- 변경된 edge: {{changed_edges}}
- 새 의존성: {{new_dependencies}}
- cross-codebase 변화: {{cross_codebase_changes}}

## 영향 범위 검증

- CodeGraph impact: {{codegraph_impact}}
- affected tests: {{affected_tests}}
- 직접 확인한 파일: {{inspected_files}}

## 테스트 결과

- 실행한 테스트: {{tests_run}}
- 통과: {{tests_passed}}
- 실패: {{tests_failed}}
- 실행하지 못한 테스트와 이유: {{tests_not_run}}

## 문서/지도 갱신

- workspace-registry.json: {{workspace_registry_status}}
- map-model.json: {{map_model_status}}
- visual-model.json: {{visual_model_status}}
- workspace-stream-map.canvas: {{workspace_canvas_status}}
- repo-domain-map.canvas: {{repo_canvas_status}}
- domain Excalidraw: {{domain_excalidraw_status}}
- business-stream Excalidraw: {{feature_excalidraw_status}}
- change Excalidraw: {{change_excalidraw_status}}
- ExcalidrawAutomate script: {{excalidraw_automate_status}}
- Documentation provider: {{documentation_provider_status}}
- Agent-native wiki: {{agent_native_wiki_status}}
- OpenWiki optional: {{openwiki_optional_status}}

## 남은 불확실성

- {{uncertainty}}

## 판정

PASS / PARTIAL / FAIL / NEEDS MANUAL REVIEW
