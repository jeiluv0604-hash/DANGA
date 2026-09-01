# DAMGA-OPS API Contract Specification v1.0

> **문서 상태**: APPROVED (Phase 2.1 Hardening)  
> **기본 Base URL**: `http://localhost:8000`  
> **API 접두사**: `/api/v1`  
> **헤더 추적**: 모든 요청 및 응답에 `X-Request-ID` 상관관계 ID 헤더가 포함됩니다.

---

## 1. 시스템 헬스체크 (Health)

### `GET /health`
- **설명**: 서비스 가동 상태 및 버전 확인
- **Response (200 OK)**:
```json
{
  "status": "ok",
  "service": "DAMGA-OPS API",
  "version": "6.0.0-prototype"
}
```

---

## 2. 데이터 수집 (Ingestion)

### `POST /api/v1/ingestions/synthetic`
- **설명**: Synthetic Golden Dataset 파이프라인 수집 및 계산 실행 (개발/테스트용)
- **Query Params**: `file_path` (default: `data/synthetic/damga_dataset.json`)
- **Response (200 OK - 신규 수집)**:
```json
{
  "ingestion_id": "INGEST-A1B2C3D4E5F6",
  "dataset_type": "SYNTHETIC",
  "status": "COMPLETED",
  "row_count": 92,
  "valid_row_count": 91,
  "blocked_row_count": 1,
  "alerts_count": 8,
  "period_alerts_count": 2,
  "source_sha256": "2132542be..."
}
```

- **Response (200 OK - 중복 요청 시 멱등성)**:
```json
{
  "status": "ALREADY_INGESTED",
  "ingestion_id": "INGEST-A1B2C3D4E5F6",
  "dataset_type": "SYNTHETIC",
  "source_sha256": "2132542be...",
  "row_count": 92,
  "valid_row_count": 91,
  "blocked_row_count": 1,
  "alerts_count": 0,
  "period_alerts_count": 0
}
```

### `GET /api/v1/ingestions`
- **설명**: 데이터 수집 이력 조회
- **Query Params**: `limit` (int, default: 50)
- **Response (200 OK)**: IngestionRunResponse 목록

---

## 3. 원천 운영 데이터 (Operations)

### `GET /api/v1/operations`
- **Query Params**: `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD)
- **Response (200 OK)**: `List[DailyOperationSchema]`

---

## 4. 계산 Facts (Facts)

### `GET /api/v1/facts`
- **Query Params**: `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD)
- **Response (200 OK)**: `List[DailyFactSchema]`

### `GET /api/v1/facts/{date}`
- **Path Params**: `date` (YYYY-MM-DD, e.g. `2026-06-12`)
- **Response (200 OK)**: `DailyFactSchema`
- **Response (404 Not Found)**: 해당 일자 Facts 부재

---

## 5. 이상 경보 (Alerts)

### `GET /api/v1/alerts`
- **Query Params**: `start_date`, `end_date`, `severity` (CRITICAL/HIGH/MEDIUM/LOW), `rule_id`
- **Response (200 OK)**: `List[AlertSchema]` (모든 Alert는 non-null `evidence_id`를 보유)

### `GET /api/v1/alerts/{date}`
- **Path Params**: `date` (YYYY-MM-DD)
- **Response (200 OK)**: `List[AlertSchema]`

### `GET /api/v1/alerts/periods`
- **설명**: 기간성 이상 경보(`R-FC-01-PERIOD`, `R-PRO-01`) 조회
- **Response (200 OK)**: `List[PeriodAlertSchema]`

---

## 6. 증적 추적 (Evidence)

### `GET /api/v1/evidence/{evidence_id}`
- **Path Params**: `evidence_id` (e.g. `EV-ALT-80E5DF84A2`)
- **Response (200 OK)**:
```json
{
  "evidence_id": "EV-ALT-80E5DF84A2",
  "evidence_type": "DAILY_ALERT",
  "business_date": "2026-08-21",
  "rule_id": "R-DQ-01",
  "file_path": "evidence/EV-ALT-80E5DF84A2.json",
  "file_sha256": "4b68e987c24f...",
  "dataset_sha256": "2132542be216b1cd5c610036f3c5207e189023a63e6a2aed1d3e87eeda2745cc",
  "created_at": "2026-09-01T14:08:06"
}
```
- **Response (404 Not Found)**: 해당 ID의 Evidence 부재

### `GET /api/v1/evidence/{evidence_id}/verify`
- **Path Params**: `evidence_id`
- **설명**: 디스크 상의 실제 Evidence 파일 바이트를 읽어 암호화 SHA-256 해시를 대조 검증 (위변조 감지)
- **Response (200 OK - 정상 무결성 검증)**:
```json
{
  "evidence_id": "EV-ALT-80E5DF84A2",
  "exists": true,
  "stored_sha256": "4b68e987c24f...",
  "actual_sha256": "4b68e987c24f...",
  "dataset_sha256": "2132542be216b1cd5c610036f3c5207e189023a63e6a2aed1d3e87eeda2745cc",
  "integrity": "VALID"
}
```
- **Response (200 OK - 파일 위변조 발생 시)**:
```json
{
  "evidence_id": "EV-ALT-80E5DF84A2",
  "exists": true,
  "stored_sha256": "4b68e987c24f...",
  "actual_sha256": "9a7f310cd41a...",
  "dataset_sha256": "2132542be216b1cd5c610036f3c5207e189023a63e6a2aed1d3e87eeda2745cc",
  "integrity": "INVALID"
}
```
- **Response (404 Not Found)**: 해당 ID의 Evidence Index 부재


---

## 7. 대시보드 (Dashboard)

### `GET /api/v1/dashboard/daily/{date}`
- **Path Params**: `date` (YYYY-MM-DD)
- **설명**: 특정 일자 일일 경영 브리핑용 종합 API (Facts + Alerts + Partial Facts Status 결합)
- **Response (200 OK - 정상 일자 2026-06-12)**:
```json
{
  "date": "2026-06-12",
  "dataset_type": "SYNTHETIC",
  "data_status": "OK",
  "blocked": false,
  "ai_eligible": true,
  "kpis": {
    "sales": 13092000.0,
    "guests": 286,
    "avg_check": 45776.22,
    "labor_cost": 4648000.0,
    "labor_ratio": 0.355,
    "food_cost": 4451280.0,
    "food_cost_ratio": 0.340,
    "contribution": 3992720.0,
    "contribution_ratio": 0.305,
    "inventory_variance_kg": -1.2,
    "waste_ratio": 0.021,
    "rating": 4.65,
    "complaints": 1
  },
  "kpi_status": {
    "sales": "AVAILABLE",
    "guests": "AVAILABLE",
    "avg_check": "AVAILABLE",
    "labor_cost": "AVAILABLE",
    "labor_ratio": "AVAILABLE",
    "food_cost": "AVAILABLE",
    "food_cost_ratio": "AVAILABLE",
    "contribution": "AVAILABLE",
    "contribution_ratio": "AVAILABLE",
    "inventory_variance": "AVAILABLE",
    "waste_ratio": "AVAILABLE",
    "rating": "AVAILABLE",
    "complaints": "AVAILABLE"
  },
  "alerts": [
    {
      "alert_id": "ALT-6A911C4F2A",
      "business_date": "2026-06-12",
      "rule_id": "R-LAB-01",
      "severity": "HIGH",
      "status": "ALERT",
      "actual_value": "0.3550259700580507",
      "threshold_value": "0.33",
      "comparison": ">=",
      "evidence_id": "EV-ALT-78A12BC84F"
    }
  ],
  "evidence_ids": ["EV-ALT-78A12BC84F"]
}
```
- **Response (200 OK - GA-007 / DATA_INCOMPLETE 일자: 2026-08-21)**:
```json
{
  "date": "2026-08-21",
  "dataset_type": "SYNTHETIC",
  "data_status": "DATA_INCOMPLETE",
  "blocked": true,
  "ai_eligible": false,
  "kpis": {
    "sales": 14162000.0,
    "guests": 419,
    "avg_check": 33799.52,
    "labor_cost": 3470000.0,
    "labor_ratio": 0.245,
    "food_cost": null,
    "food_cost_ratio": null,
    "contribution": null,
    "contribution_ratio": null,
    "inventory_variance_kg": -0.9,
    "waste_ratio": 0.006,
    "rating": 4.56,
    "complaints": 2
  },
  "kpi_status": {
    "sales": "AVAILABLE",
    "guests": "AVAILABLE",
    "avg_check": "AVAILABLE",
    "labor_cost": "AVAILABLE",
    "labor_ratio": "AVAILABLE",
    "food_cost": "MISSING_INPUT",
    "food_cost_ratio": "BLOCKED_DEPENDENCY",
    "contribution": "BLOCKED_DEPENDENCY",
    "contribution_ratio": "BLOCKED_DEPENDENCY",
    "inventory_variance": "AVAILABLE",
    "waste_ratio": "AVAILABLE",
    "rating": "AVAILABLE",
    "complaints": "AVAILABLE"
  },
  "alerts": [
    {
      "alert_id": "ALT-DQ-01",
      "business_date": "2026-08-21",
      "rule_id": "R-DQ-01",
      "severity": "CRITICAL",
      "status": "ALERT",
      "actual_value": "{\"date\": \"46255\", \"blocked_reason\": \"Missing mandatory field: Food_Cost\"}",
      "threshold_value": "Non-null",
      "comparison": "is_valid",
      "evidence_id": "EV-ALT-0098CD246C"
    }
  ],
  "evidence_ids": ["EV-ALT-0098CD246C"]
}
```

### `GET /api/v1/dashboard/summary`
- **Query Params**: `start_date`, `end_date`
- **설명**: 지정 기간 동안의 총매출, 일평균 매출, 평균 인건비율, 평균 원가율, 총공헌이익, 심각도별 Alert 집계 및 KPI Coverage 메타데이터.
- **Response (200 OK)**:
```json
{
  "start_date": "2026-06-01",
  "end_date": "2026-08-31",
  "dataset_type": "SYNTHETIC",
  "total_days": 92,
  "data_complete_days": 91,
  "data_incomplete_days": 1,
  "total_sales": 1058152000.0,
  "average_daily_sales": 11501652.17,
  "average_labor_ratio": 0.2838,
  "average_food_cost_ratio": 0.3475,
  "total_contribution": 390124800.0,
  "average_contribution_ratio": 0.3692,
  "critical_alert_count": 2,
  "high_alert_count": 6,
  "medium_alert_count": 3,
  "coverage": {
    "sales": {
      "available_days": 92,
      "total_days": 92
    },
    "labor_ratio": {
      "available_days": 92,
      "total_days": 92
    },
    "food_cost_ratio": {
      "available_days": 91,
      "total_days": 92
    },
    "contribution_ratio": {
      "available_days": 91,
      "total_days": 92
    }
  }
}
```

---

## 8. 경영체계 프로토타입

- `GET /api/v1/management/prototype`: 담가화로구이 경영체계 전체 Synthetic Snapshot
- `GET /api/v1/management/finance`: 월 손익·Budget vs Actual·Cash Flow
- `GET /api/v1/management/menus`: Recipe/BOM 원가 및 ABCD
- `GET /api/v1/management/organization`: 조직·RACI·관리자 Scorecard·전결정책
- `GET /api/v1/management/standards`: SOP·체크리스트
- `GET /api/v1/management/actions`: Action Closure 목록
- `POST /api/v1/management/actions/{action_id}/transition`: 허용 상태 전이 및 감사 이벤트
- `GET /api/v1/management/actions/{action_id}/audit`: Action SHA-256 감사 체인
- `GET /api/v1/management/reviews/monthly`: 월간 경영회의 및 결정론적 Management Brief

모든 응답은 `dataset_type=SYNTHETIC`을 유지한다. 비용 배부·메뉴 ABCD·관리자 KPI 가중치는 `UNVERIFIED POLICY`다.

