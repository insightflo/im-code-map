# Deprecated template: use business-stream.template.md

v5에서 `feature-flow`는 독립 모델이 아니다. 사용자 또는 시스템의 구체적 trigger부터 terminal outcome까지 이어지는 **business stream**으로 작성한다.

새 문서는 `templates/business-stream.template.md`를 사용한다. 기존 v3 문서를 이 형식으로 마이그레이션할 때 확인되지 않은 actor, guard, state, error, retry, compensation은 `UNVERIFIED`로 남긴다.
