# Shadow Mode Architecture Specification v1.0

## 1. 목적 (Mission)
실제 매장 데이터를 수신하더라도 기존 검증된 Synthetic Ground Truth 파이프라인을 손상시키지 않고 병렬로 검증(Shadowing)합니다.

## 2. 핵심 통제 규칙
1. **No Truth Overwrite**: `dataset_type = 'SHADOW_REAL'` 데이터는 CEO Dashboard의 기존 공인 진실 데이터를 덮어쓰지 않습니다.
2. **AI Action Blocking**: Shadow Mode 데이터에서는 AI Analyst의 운영 변경 조치 권고가 비활성화됩니다 (`ai_eligible = False`).
3. **Synthetic Calibration Badge**: UI 및 리포트에 `SHADOW REAL - 실제 데이터 검증 중 · 운영 판단용 아님` 뱃지가 강제 표시됩니다.
4. **Reconciliation Gate**: Shadow 데이터가 완전히 MAPPED 및 RECONCILED 검증을 거치기 전에는 `UNVERIFIED` 상태를 유지합니다.
