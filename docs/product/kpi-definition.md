# KPI Definition V1.0 (담가화로 경영 지표 정의서)

## 1. 핵심 경영 지표 목록

| KPI명 | 영문 필드명 | 도메인 | 산식 (Formula) | 단위 | 상태 | 비고 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **순매출** | `Sales` (`net_sales`) | Sales | SUM(item_price * qty - discount) | 원 (KRW) | `READY` | 기본 일일 실적 |
| **객수** | `Guests` | Sales | SUM(guest_count) | 명 | `READY` | 방문 고객 수 |
| **객단가** | `Avg_Check` | Sales | Sales / Guests | 원/명 | `READY` | 1인당 평균 결제액 |
| **인건비** | `Labor_Cost` | Labor | SUM(work_hours * hourly_wage + allowance) | 원 (KRW) | `READY` | 당일 총 인건비 |
| **인건비율** | `Labor_Ratio` | Labor | Labor_Cost / Sales | % | `READY` | 정상 기준: 27.0% |
| **식재료비** | `Food_Cost` | FoodCost | SUM(used_qty * unit_purchase_price) | 원 (KRW) | `READY` | 당일 식재료 원가 |
| **식재료 원가율** | `Food_Cost_Ratio` | FoodCost | Food_Cost / Sales | % | `READY` | 정상 기준: 32.5% |
| **공헌이익** | `Contribution` | Management | Sales - (Food_Cost + Labor_Cost) | 원 (KRW) | `READY` | 1차 영업 수익성 |
| **공헌이익률** | `Contribution_Ratio`| Management | Contribution / Sales | % | `READY` | 정상 기준: 약 40.5% |
| **입고량** | `Incoming_kg` | Inventory | SUM(incoming_weight) | kg | `READY` | 당일 육류 입고량 |
| **판매량** | `Sold_kg` | Inventory | SUM(menu_sold_qty * recipe_portion) | kg | `READY` | 레시피 기반 판매량 |
| **서비스량** | `Service_kg` | Inventory | SUM(service_portion) | kg | `READY` | 고객 서비스 제공량 |
| **폐기량** | `Waste_kg` | Inventory | SUM(waste_weight) | kg | `READY` | 손질 로스 및 변질 폐기 |
| **이론재고** | `Theory_End_kg` | Inventory | Prev_End + Incoming - (Sold + Service + Waste) | kg | `READY` | 계산상 잔여 재고 |
| **실사재고** | `Actual_End_kg` | Inventory | Physical Count Weight | kg | `READY` | 마감 실측 재고 |
| **재고차이** | `Variance_kg` | Inventory | Actual_End_kg - Theory_End_kg | kg | `READY` | 허용 오차: +-1.5kg |
| **폐기율** | `Waste_Ratio` | Inventory | Waste_kg / Sold_kg | % | `READY` | 경보 기준: >= 5.0% |
| **고객 평점** | `Rating` | Customer | Daily Average Star Rating | 점 (1~5) | `READY` | 정상 하한: 4.4점 |
| **리뷰 수** | `Review_Count` | Customer | SUM(new_reviews) | 건 | `READY` | 신규 등록 리뷰 수 |
| **클레임 건수** | `Complaints` | Customer | SUM(complaint_voc_count) | 건 | `READY` | 경보 기준: >= 5건/일 |

---

## 2. Phase 2 확장 KPI (NEXT / UNVERIFIED)
- `Hourly_Sales_Per_Labor`: 시간당 인력 매출 (`sales / labor_hours`)
- `Menu_Contribution_Margin`: 메뉴별 개별 공헌이익 (`price - standard_cost`)
- `Meat_Yield_Rate`: 육류 손질 수율 (`usable_weight / raw_weight`)
- `Complaint_Per_Guest`: 객수 대비 클레임 발생률 (`complaints / guests`)
