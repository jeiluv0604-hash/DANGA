# Data Reconciliation Contract Specification v1.0

## 1. 대사(Reconciliation) 목표
원천 파일의 상세 거래 내역 합계와 일일 요약/계산서 합계 간의 일치성을 검증하여 데이터 누락 및 위변조를 방지합니다.

## 2. 도메인별 대사 규칙
- **POS**: `SUM(net_sales)` vs 일일 마감 매출 (Diff = 0: MATCH, <= 2%: MINOR_MISMATCH, > 2%: MAJOR_MISMATCH)
- **Attendance**: `SUM(worked_minutes)` vs 부서별 일일 총 근무시간
- **Purchases**: `quantity * unit_price` vs 세금계산서 공급가액 (`amount`)
- **Inventory**: `actual_end` vs `opening + incoming - sold - service - waste - staff + transfer`

## 3. 대사 상태
- `MATCH`: 완벽 일치 (차이 0 또는 1원 미만)
- `MINOR_MISMATCH`: 2% 이내의 미세 불일치 (원단위 절사 등)
- `MAJOR_MISMATCH`: 2% 초과의 중대한 불일치 (수입 및 검토 필요)
- `NOT_COMPARABLE`: 필수 필드 부재로 대사 불가 (DATA_INCOMPLETE)
