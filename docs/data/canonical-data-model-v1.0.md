# Canonical Data Model Specification v1.0

## 1. 개요 (Overview)
DAMGA-OPS는 특정 POS/근태/ERP 벤더(OKPOS, EasyPOS 등)에 종속되지 않는 4대 도메인 표준 Canonical Data Schema를 정의합니다.
모든 원천 데이터 파일은 Source Adapter와 Mapping Manifest를 통해 Canonical Model로 변환되어 저장 및 검증됩니다.

---

## 2. 4대 도메인 Canonical Schemas

### 2.1 POS 거래 명세 (Canonical POS)
- **business_date**: 영업일자 (YYYY-MM-DD)
- **transaction_time**: 결제시간 (HH:MM:SS)
- **receipt_id**: 영수증/주문 식별자
- **table_id**: 테이블/좌석 번호
- **menu_id**: 메뉴 고유 코드
- **menu_name**: 메뉴 품명
- **quantity**: 주문 수량 (정수, > 0)
- **gross_sales**: 총매출액 (할인 전)
- **discount**: 할인액 (기본 0.0)
- **net_sales**: 실매출액 (결제금액)
- **guests**: 고객/객수
- **payment_type**: CARD, CASH, SIMPLE 등
- **cancelled**: 취소 여부 (Boolean)
- **source_system**: 원천 시스템 식별자
- **source_file**: 원천 파일명
- **source_row**: 원천 파일 행 번호

### 2.2 근태 기록 (Canonical Attendance)
- **business_date**: 근무일자 (YYYY-MM-DD)
- **employee_id**: 직원 식별번호 (개인 실명 저장 금지)
- **department**: 소속 부서 (홀 / 주방 / 관리)
- **role**: 직책 (매니저 / 조리사 / 서버 등)
- **clock_in**: 출근 시각 (HH:MM)
- **clock_out**: 퇴근 시각 (HH:MM)
- **worked_minutes**: 실근무시간 (분)
- **regular_minutes**: 소정근무시간 (분)
- **overtime_minutes**: 연장근무시간 (분)
- **labor_cost**: 일 인건비 지급액 (미입력 시 None 유지, 임의 추정 금지)
- **source_system / source_file / source_row**: 감사 추적 필드

### 2.3 매입 거래 (Canonical Purchase)
- **purchase_date**: 매입일자 (YYYY-MM-DD)
- **supplier_id**: 공급처/거래처 코드
- **category**: 품목 대분류 (육류, 채소, 주류, 공산품 등)
- **item_id**: 자재/품목 식별코드
- **item_name**: 자재 품명
- **quantity**: 입고 수량 (> 0)
- **unit**: 규격 단위 (kg, g, box, ea, pack 등)
- **unit_price**: 입고 단가 (원)
- **amount**: 공급가액 (원)
- **tax**: 부가세액 (원)
- **source_amount**: 원천 세금계산서 청구금액
- **calculated_amount**: 수량 × 단가 재계산 검증액
- **invoice_id**: 계산서/전표 번호

### 2.4 재고 실사 (Canonical Inventory)
- **business_date**: 실사일자 (YYYY-MM-DD)
- **item_id**: 자재 식별코드
- **item_name**: 자재명
- **opening_qty**: 기초 재고량 (전일 실사재고)
- **incoming_qty**: 당일 총 입고량
- **sold_qty**: POS 레시피 기준 출고량
- **service_qty**: 서비스 제공량 (미기록 시 null, 0 처리 금지)
- **waste_qty**: 폐기량 (미기록 시 null)
- **staff_meal_qty**: 직원 식사량
- **transfer_qty**: 매장 간/창고 간 이동량
- **theory_end_qty**: 이론 장부 재고량
- **actual_end_qty**: 마감 실사 재고량
- **unit**: 단위 (kg, box 등)

---

## 3. 계통성 및 무결성 (Lineage & Integrity)
- 모든 Canonical 레코드는 import_id, source_file, source_row, dataset_type, erification_status를 포함하여 원천 파일의 각 행으로 100% 역추적 가능합니다.
