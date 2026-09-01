# DAMGA-OPS Storage Design Specification v1.0

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
