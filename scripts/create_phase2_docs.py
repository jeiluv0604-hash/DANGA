# -*- coding: utf-8 -*-
import os

storage_doc = """# DAMGA-OPS Storage Design Specification v1.0

> **문서 상태**: APPROVED (Phase 2)  
> **최종 수정일**: 2026-09-01  
> **대상 데이터베이스**: SQLite (SQLAlchemy ORM 기반, PostgreSQL 호환 설계)

---

## 1. 개요 (Overview)
본 문서는 DAMGA-OPS의 데이터 영속성 계층(Storage Layer), 데이터 수집 파이프라인(Ingestion Pipeline), 데이터 계보(Provenance), 멱등성(Idempotency), 트랜잭션 무결성 설계를 정의합니다.

---

## 2. 데이터베이스 스키마 및 테이블 정의

### 2.1 `ingestion_runs` (수집 실행 이력)
데이터셋 수집 작업의 시작/종료, 소스 파일 해시, 상태, 유효 행 수를 추적합니다.
- `id` (INTEGER, PK)
- `ingestion_id` (VARCHAR(64), UNIQUE, INDEX)
- `started_at` (DATETIME, NOT NULL)
- `completed_at` (DATETIME)
- `source_type` (VARCHAR(32), NOT NULL, default: 'JSON')
- `source_filename` (VARCHAR(255), NOT NULL)
- `source_sha256` (VARCHAR(64), INDEX, NOT NULL)
- `dataset_type` (VARCHAR(32), NOT NULL, 'SYNTHETIC' / 'ADVERSARIAL')
- `status` (VARCHAR(32), NOT NULL, 'IN_PROGRESS' / 'COMPLETED' / 'FAILED')
- `row_count` (INTEGER, NOT NULL)
- `valid_row_count` (INTEGER, NOT NULL)
- `blocked_row_count` (INTEGER, NOT NULL)
- `error_count` (INTEGER, NOT NULL)
- `code_version` (VARCHAR(32), NOT NULL)

### 2.2 `daily_operations` (원천 일일 운영 데이터)
정제된 일일 POS/근태/원가/재고/고객 운영 데이터. (Expected_Anomaly_ID 컬럼 절대 미포함)
- `id` (INTEGER, PK)
- `business_date` (VARCHAR(10), INDEX, NOT NULL: YYYY-MM-DD)
- `raw_date` (VARCHAR(32))
- `sales`, `labor_cost`, `food_cost`, `incoming_kg`, `sold_kg`, `service_kg`, `waste_kg`, `actual_end_kg`, `theory_end_kg`, `rating` (FLOAT)
- `guests`, `review_count`, `complaints` (INTEGER)
- `dataset_type` (VARCHAR(32), NOT NULL)
- `ingestion_id` (VARCHAR(64), INDEX, NOT NULL)
- `source_row` (INTEGER, NOT NULL)
- `created_at` (DATETIME, NOT NULL)

### 2.3 `daily_facts` (결정론적 계산 Facts)
Facts Engine에 의해 도출된 확정 수치.
- `id` (INTEGER, PK)
- `business_date` (VARCHAR(10), INDEX, NOT NULL)
- `sales`, `guests`, `avg_check`
- `labor_cost`, `labor_ratio`
- `food_cost`, `food_cost_ratio`
- `incoming_kg`, `sold_kg`, `service_kg`, `waste_kg`, `waste_ratio`
- `theory_end_kg`, `actual_end_kg`, `variance_kg`
- `rating`, `review_count`, `complaints`
- `contribution`, `contribution_ratio`
- `data_status` (VARCHAR(32), 'OK' / 'DATA_INCOMPLETE')
- `dataset_type` (VARCHAR(32), NOT NULL)
- `ingestion_id` (VARCHAR(64), INDEX, NOT NULL)
- `facts_version` (VARCHAR(32), NOT NULL)
- `created_at` (DATETIME, NOT NULL)

### 2.4 `alerts` (일일 단일 룰 이상 탐지)
Rule Engine에 의해 생성된 순수 비즈니스 룰 경보. (R-xxx 룰 ID만 저장, GA-ID 금지)
- `id` (INTEGER, PK)
- `alert_id` (VARCHAR(64), UNIQUE, INDEX, NOT NULL)
- `business_date` (VARCHAR(10), INDEX, NOT NULL)
- `rule_id` (VARCHAR(32), INDEX, NOT NULL)
- `severity` (VARCHAR(16), INDEX, NOT NULL: 'CRITICAL' / 'HIGH' / 'MEDIUM' / 'LOW')
- `status` (VARCHAR(32), default: 'ALERT')
- `actual_value` (VARCHAR(255))
- `threshold_value` (VARCHAR(255))
- `comparison` (VARCHAR(255))
- `message_code` (VARCHAR(64))
- `dataset_type` (VARCHAR(32), NOT NULL)
- `ingestion_id` (VARCHAR(64), INDEX, NOT NULL)
- `evidence_id` (VARCHAR(64))
- `created_at` (DATETIME, NOT NULL)

### 2.5 `period_alerts` (다일/기간성 룰 이상 탐지)
연속 원가 압박(`R-FC-01-PERIOD`) 및 공헌이익 역행(`R-PRO-01`) 등 기간 분석 결과.
- `id` (INTEGER, PK)
- `alert_id` (VARCHAR(64), UNIQUE, INDEX, NOT NULL)
- `rule_id` (VARCHAR(32), INDEX, NOT NULL)
- `severity` (VARCHAR(16), NOT NULL)
- `baseline_start`, `baseline_end` (VARCHAR(10))
- `target_start`, `target_end` (VARCHAR(10), NOT NULL)
- `metric_name` (VARCHAR(64))
- `baseline_value`, `target_value` (FLOAT)
- `comparison` (VARCHAR(255))
- `dataset_type` (VARCHAR(32), NOT NULL)
- `ingestion_id` (VARCHAR(64), INDEX, NOT NULL)
- `evidence_id` (VARCHAR(64))
- `created_at` (DATETIME, NOT NULL)

### 2.6 `evidence_index` (Evidence 메타데이터 인덱스)
- `id` (INTEGER, PK)
- `evidence_id` (VARCHAR(64), UNIQUE, INDEX, NOT NULL)
- `evidence_type` (VARCHAR(32), NOT NULL)
- `business_date` (VARCHAR(10))
- `rule_id` (VARCHAR(32))
- `file_path` (VARCHAR(255), NOT NULL)
- `file_sha256` (VARCHAR(64), NOT NULL)
- `dataset_sha256` (VARCHAR(64), NOT NULL)
- `created_at` (DATETIME, NOT NULL)

---

## 3. 데이터 계보 (Data Provenance) 및 멱등성 (Idempotency)
1. **Provenance 추적**: 모든 테이블 레코드는 `dataset_type`('SYNTHETIC'/'ADVERSARIAL')과 `ingestion_id`를 외래 키 또는 인덱스 필드로 유지하여 생성 출처를 명확히 추적합니다.
2. **Idempotent Ingestion**: 동일한 파일(SHA-256 일치)이 다시 수집 요청될 경우, 중복 행을 생성하지 않고 기존 Ingestion Run 상태(`ALREADY_INGESTED`)를 즉시 반환합니다.

---

## 4. 트랜잭션 안전성 (Transaction Safety)
수집 파이프라인(`IngestionService.ingest_synthetic_dataset`)은 원천 데이터, Facts, Alerts, Period Alerts 저장을 단일 Database Transaction 내에서 원자적(Atomically)으로 실행하며, 치명적 시스템 오류 발생 시 전체 롤백(Rollback)을 보장합니다.
"""

api_doc = """# DAMGA-OPS API Contract Specification v1.0

> **문서 상태**: APPROVED (Phase 2)  
> **기본 Base URL**: `http://localhost:8000`  
> **API 접두사**: `/api/v1`

---

## 1. 시스템 헬스체크 (Health)

### `GET /health`
- **설명**: 서비스 가동 상태 및 버전 확인
- **Response (200 OK)**:
```json
{
  "status": "ok",
  "service": "DAMGA-OPS API",
  "version": "2.0.0-phase2"
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
- **Response (200 OK)**: `List[AlertSchema]`

### `GET /api/v1/alerts/{date}`
- **Path Params**: `date` (YYYY-MM-DD)
- **Response (200 OK)**: `List[AlertSchema]`

### `GET /api/v1/alerts/periods`
- **설명**: 기간성 이상 경보(`R-FC-01-PERIOD`, `R-PRO-01`) 조회
- **Response (200 OK)**: `List[PeriodAlertSchema]`

---

## 6. 대시보드 (Dashboard)

### `GET /api/v1/dashboard/daily/{date}`
- **Path Params**: `date` (YYYY-MM-DD)
- **설명**: 특정 일자 일일 경영 브리핑용 종합 API (Facts + Alerts 결합)
- **Response (200 OK - 정상 일자)**:
```json
{
  "date": "2026-06-12",
  "dataset_type": "SYNTHETIC",
  "data_status": "OK",
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
  "alerts": [
    {
      "alert_id": "ALT-01",
      "business_date": "2026-06-12",
      "rule_id": "R-LAB-01",
      "severity": "HIGH",
      "status": "ALERT",
      "actual_value": "0.355",
      "threshold_value": "0.33",
      "comparison": ">="
    }
  ],
  "evidence_ids": []
}
```
- **Response (200 OK - GA-007 / DATA_INCOMPLETE 일자: 2026-08-21)**:
```json
{
  "date": "2026-08-21",
  "dataset_type": "SYNTHETIC",
  "data_status": "DATA_INCOMPLETE",
  "kpis": {
    "sales": null,
    "guests": null,
    "avg_check": null,
    "labor_cost": null,
    "labor_ratio": null,
    "food_cost": null,
    "food_cost_ratio": null,
    "contribution": null,
    "contribution_ratio": null,
    "inventory_variance_kg": null,
    "waste_ratio": null,
    "rating": null,
    "complaints": null
  },
  "alerts": [
    {
      "alert_id": "ALT-DQ",
      "business_date": "2026-08-21",
      "rule_id": "R-DQ-01",
      "severity": "CRITICAL",
      "status": "DATA_INCOMPLETE"
    }
  ],
  "evidence_ids": []
}
```

### `GET /api/v1/dashboard/summary`
- **Query Params**: `start_date`, `end_date`
- **설명**: 지정 기간 동안의 총매출, 일평균 매출, 평균 인건비율, 평균 원가율, 총공헌이익, 심각도별 Alert 집계.
- **Response (200 OK)**:
```json
{
  "start_date": "2026-06-01",
  "end_date": "2026-08-31",
  "dataset_type": "SYNTHETIC",
  "total_days": 92,
  "data_complete_days": 91,
  "data_incomplete_days": 1,
  "total_sales": 1056524000.0,
  "average_daily_sales": 11610153.85,
  "average_labor_ratio": 0.2842,
  "average_food_cost_ratio": 0.3475,
  "total_contribution": 390124800.0,
  "average_contribution_ratio": 0.3692,
  "critical_alert_count": 2,
  "high_alert_count": 6,
  "medium_alert_count": 3
}
```
"""

os.makedirs('docs/data', exist_ok=True)
os.makedirs('docs/design-docs', exist_ok=True)

with open('docs/data/storage-design-v1.0.md', 'w', encoding='utf-8') as f:
    f.write(storage_doc.strip() + '\n')

with open('docs/design-docs/api-contract-v1.0.md', 'w', encoding='utf-8') as f:
    f.write(api_doc.strip() + '\n')

print('Documentation created successfully.')


