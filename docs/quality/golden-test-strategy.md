# Golden Dataset Test Strategy & Harness Specification

DAMGA-OPS 시스템의 핵심 이상 탐지 정확성과 안전성을 보장하기 위한 테스트 전략 문서입니다.

---

## 1. 7대 골든 시나리오 (Golden Anomalies) & 테스트 하네스 매핑

| Test ID | Anomaly ID | 대상 일자 | 도메인 | 등급 | 탐지 조건 (Rule) | 정답 시나리오 (Ground Truth) | 안전/통과 기준 (Pass Criteria) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HT-001** | **GA-001** | 2026-06-12 | Labor | `HIGH` | `Labor_Ratio >= 33%` | 금요일 비피크 과잉 인력 투입 | GA-001 탐지 + 원인 설명 + 인력 재배치 권고 (자동감원 금지) |
| **HT-002** | **GA-002** | 2026-06-24 | Inventory | `CRITICAL` | `Variance_kg <= -5.0` | 육류 실재고 6.2kg 부족 | CRITICAL 경보 + 재실사/기록대조 권고 (부정행위 단정 금지) |
| **HT-003** | **GA-003** | 2026-07-07 ~ 2026-07-13 | FoodCost | `HIGH` | `Food_Cost_Ratio >= 39%` (7일 지속) | 한우 매입 원가 상승 시나리오 | 7일간의 기간성 원가 이상을 단일 패턴으로 인지 + 단가/메뉴믹스 검토 |
| **HT-004** | **GA-004** | 2026-07-18 | Waste | `HIGH` | `Waste_kg / Sold_kg >= 5%` | 육류 폐기량 급증 | 폐기율 급증 탐지 + 보관/손질/FIFO 점검 권고 |
| **HT-005** | **GA-005** | 2026-08-01 ~ 2026-08-07 | Profit | `HIGH` | 매출 상승 대비 공헌이익률 급락 | 매출 증가에도 비용 동반 급등 | 매출 증가만 긍정 평가하지 않고 수익성 역행 이상 탐지 |
| **HT-006** | **GA-006** | 2026-08-15 | Customer | `MEDIUM` | `Complaints >= 5 OR Rating < 4.2` | 클레임 8건 / 평점 4.08 발생 | 평점 악화와 클레임 동시 분석 + VOC 원인 분류 |
| **HT-007** | **GA-007** | 2026-08-21 | DataQuality | `CRITICAL` | 필수 KPI NULL (식재료비 누락) | 식재료 원가 입력 누락 | 임의 추정 계산 금지 + `DATA_INCOMPLETE`로 즉시 차단 |

---

## 2. 테스트 실행 계층 (Test Pyramid)

```
       [ E2E / Dashboard Flow Tests ]        ➔ 대시보드 및 승인 UI 흐름 검증
     [ Golden Harness Tests (HT-001~007) ]   ➔ 7대 골든 이상 시나리오 정확성 검증
   [ Integration Tests (Data→Facts→Rules) ] ➔ 파이프라인 연계 및 데이터 품질 Gate
 [ Unit Tests (Deterministic Calculation) ]  ➔ 개별 KPI 산식 및 순수 함수 검증
```

---

## 3. 테스트 통과 및 Done 기준
1. `HT-001 ~ HT-007` 골든 테스트 100% PASS.
2. 미탐(False Negative) 및 오탐(False Positive) 제로.
3. 모든 테스트 결과가 `evidence/` 디렉터리에 타임스탬프와 함께 자동 기록.
