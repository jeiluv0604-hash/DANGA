# Source Adapter Contract Specification v1.0

## 1. Adapter 아키텍처 원칙
1. **Generic-First**: 특정 벤더(OKPOS, EasyPOS 등) 하드코딩 금지. Generic CSV Adapter 및 Generic XLSX Adapter 기반으로 확장.
2. **Deterministic Transformation**: 원천 컬럼 파싱과 정규화는 결정론적 매핑 매니페스트에 의해 수행.
3. **Quarantine Isolation**: 개별 레코드의 결함(날짜 오류, 음수 매출, 중복)이 전체 배치를 실패시키지 않고 격리(Quarantine).
4. **Zero Accusations & Privacy**: PII 검출 시 수입 차단 및 안전 마스킹.

## 2. 인터페이스 명세
- `detect_source_type(file_path)` -> `POS | ATTENDANCE | PURCHASE | INVENTORY | UNKNOWN`
- `profile(file_path, sheet_name)` -> `DataProfile`
- `map_to_canonical(file_path, manifest, sheet_name)` -> `MappingResult`
