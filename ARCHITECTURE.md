# ARCHITECTURE.md — DAMGA-OPS System Architecture

## 1. 시스템 개요 및 설계 철학
DAMGA-OPS는 **Harness Engineering** 원칙에 기반하여 설계된 외식업 경영 자동화 인텔리전스 시스템입니다.

> **핵심 철학**: “AI가 숫자를 만드는 시스템”이 아니라 **“정확한 계산 엔진(Facts Engine)이 산출한 사실을 AI가 경영 언어로 해석하는 시스템”**

---

## 2. 책임 분리 아키텍처 (Layered Architecture)

```
[Raw Sources: POS, Attendance, Purchases, Inventory, Reviews]
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Data Layer & Validation Gate     │ ➔ 누락/오류 시 DATA_INCOMPLETE 차단
          └───────────────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Facts Engine (Deterministic)     │ ➔ 코드/SQL 기반 100% 결정론적 계산
          └───────────────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Rule Engine (Threshold & Match)  │ ➔ 7대 Golden Anomaly 및 경보 탐지
          └───────────────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  AI Analyst Layer (LLM)           │ ➔ 사실 해석, 원인 후보, 조치안 제안
          └───────────────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Human Approval & Cockpit UI      │ ➔ 대표/관리자 검토 및 실행 승인
          └───────────────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Evidence & Audit Store           │ ➔ 전 과정 추적성 및 재현성 보장
          └───────────────────────────────────┘
```

### 레이어별 세부 역할 및 제약
1. **Data Layer (`domains/*/data`, `domains/data_quality`)**:
   - 원천 CSV/XLSX/JSON 파일 수집, 스키마 검증, 필드별 유효성 검사.
   - 필수 필드 누락 시 `data_status: DATA_INCOMPLETE`, `blocked: True`, `ai_eligible: False` 플래그 설정 및 `R-DQ-01` 경보 발행.
   - **Partial Facts 원칙**: 독립적으로 유효한 관측치는 보존하고, 결측 필드에 직접 종속된 파생 지표만 `Null`로 보존 (`docs/data/kpi-dependency-contract-v1.0.md`).
2. **Facts Engine (`domains/*/facts`)**:
   - 매출, 인건비율, 식재료 원가율, 공헌이익, 재고차이 등 경영 지표를 결정론적 순수 함수로 계산.
   - LLM에 계산 위임 절대 금지 (GP-01).
3. **Rule Engine (`domains/*/rules`)**:
   - 사전 정의된 임계값(R-LAB-01, R-INV-01, R-FC-01, R-WST-01, R-CUS-01, R-DQ-01, R-PRO-01, R-FC-01-PERIOD)에 따라 경보(Alert) 판정.
   - 모든 Alert는 고유한 `evidence_id`를 보유하며 `evidence_index`와 1:1 연결됨.
4. **AI Analyst Layer (`domains/analyst`, `apps/api/services/analyst_service.py`)**:
   - Facts와 Rules 결과 JSON을 입력받아 경영 언어로 1~2문장 요약, 원인 가설, 조치안 제시.
   - **Semantic FactRef Grounding**: 지표명, 수치, 일자, 증적ID를 다차원 바인딩하여 환각 및 의미 왜곡(Semantic Swap) 원천 차단.
   - **Provider Failure Hardening**: Silent Fallback을 금지하고 `PROVIDER_UNAVAILABLE` 및 명시적 실패 사유 반환.
   - **Prompt Injection Isolation**: 비정형 텍스트를 `<UNTRUSTED_BUSINESS_DATA>` 태그로 격리.
   - `ai_eligible == False`인 일자는 AI 추천 생성을 사전에 안전하게 차단 (`DATA_INCOMPLETE -> BLOCKED`).
5. **Decision Integrity & Evidence Store (`evidence/`, `decision_audit_logs`, `evidence_index`)**:
   - **State Machine**: `REVIEW_REQUIRED -> APPROVED | REJECTED` 엄격 적용 및 중복 승인 차단 (409 Conflict).
   - **Tamper-Evident Hash Chain**: `SHA256(previous_hash + brief_id + action_type + actor_role + timestamp + comment)` 기반의 Application-level Append-Only Audit Log.
   - 모든 Evidence 파일의 SHA-256 해시를 인덱싱하여 불변성 및 전 과정 추적성 보장.
   - 모든 계산 입력값, 룰 판정, 이상 탐지 결과, 테스트 결과를 타임스탬프와 해시로 보존 및 API로 조회 가능.

---

## 3. 백엔드 아키텍처 및 계층 분리 (Backend & Storage Architecture)

DAMGA-OPS 백엔드는 계산 책임과 서빙 책임을 엄격하게 분리합니다.

```
[REST API Client / Dashboard]
            │ (X-Request-ID Header 추적)
            ▼
┌───────────────────────────────────────────────┐
│ Routes (FastAPI: /api/v1/*)                   │ ➔ 입력 검증, 쿼리 파싱, 응답 직렬화
└───────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────┐
│ Services (Ingestion / Dashboard / Analytics)  │ ➔ 비즈니스 워크플로우 오케스트레이션
└───────────────────────────────────────────────┘
            │                       │
            ▼                       ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│ Domains (Facts & Rules) │   │ Repositories (CRUD)     │
│ ➔ 100% 결정론적 순수 함수│   │ ➔ SQLAlchemy ORM        │
└─────────────────────────┘   └─────────────────────────┘
                                    │
                                    ▼
                              ┌─────────────────────────┐
                              │ Storage (SQLite DB)     │
                              │ ➔ data/damga_ops.db     │
                              └─────────────────────────┘
```

### 3.1 디렉터리 구조

```
DAMGA-OPS/
├─ AGENTS.md                  # 에이전트 작업 헌장 및 탐색 지도
├─ README.md                  # 프로젝트 개요 및 실행 가이드
├─ ARCHITECTURE.md            # 시스템 아키텍처 및 책임 분리 정의
├─ alembic.ini                # Alembic 데이터베이스 마이그레이션 구성
├─ migrations/                # Alembic 비파괴적 스키마 마이그레이션 버전
├─ mappings/                  # 4대 도메인 표준 매핑 매니페스트 (JSON)
├─ fixtures/source_samples/   # 실무 형태의 원천 CSV/XLSX 샘플 데이터셋
├─ docs/                      # 세부 문서화
│  ├─ product/                # 마스터 명세서, KPI 정의
│  ├─ data/                   # 데이터 계약, Canonical 스키마, 대사/섀도우 규격
│  ├─ design-docs/            # API 명세서 (api-contract-v1.0.md)
│  ├─ exec-plans/             # 실행 계획 (active / completed)
│  ├─ security/               # PII 보호 및 실데이터 보안 정책
│  ├─ operations/             # 매장 실데이터 온보딩 가이드
│  └─ quality/                # 골든 원칙, 테스트 전략, 증거 정책
├─ apps/                      # 애플리케이션 계층
│  ├─ frontend/               # React + Vite + TypeScript CEO Cockpit Web Dashboard
│  │  ├─ src/
│  │  │  ├─ components/       # UI Presentation 컴포넌트 (kpi, alerts, charts, panels, drawer, shadow badge)
│  │  │  ├─ hooks/            # Data Fetching 커스텀 훅 (useDailyDashboard, useRecentTrends, useSummary)
│  │  │  ├─ api/              # REST API 클라이언트
│  │  │  ├─ utils/            # Missing!=Zero 서식 포맷터 & 룰 한글화 메타데이터
│  │  │  └─ pages/            # 메인 대시보드 페이지 (CeoCockpitPage)
│  │  └─ tests/               # Vitest 컴포넌트 테스트 (UI-001~015) & Playwright E2E
│  └─ api/                    # FastAPI Backend Application
│     ├─ config.py            # 앱 설정 및 환경변수
│     ├─ database.py          # SQLAlchemy 엔진, 세션, Base
│     ├─ dependencies.py      # DB 의존성 주입
│     ├─ logger.py            # JSON 구조화 로거 (Structured Logging)
│     ├─ models/              # ORM 엔티티 (ingestion, ops, facts, alerts, evidence, canonical, imports)
│     ├─ schemas/             # Pydantic 요청/응답 스키마
│     ├─ repositories/        # DB 접근 계층 (imports_repository 등)
│     ├─ services/            # Ingestion, Dashboard, Analyst, Import 서비스 계층
│     └─ routes/              # REST API 엔드포인트 라우터 (/imports, /mappings 포함)
├─ domains/                   # 비즈니스 도메인 로직 (Facts & Rules)
│  ├─ adapters/               # Generic Source Adapters, Profiling, Mapping, Quarantine, Reconciliation, Shadow
│  ├─ data_quality/           # Data Quality Gate & 스키마 검증
│  ├─ sales/                  # 매출, 객수, 객단가
│  ├─ labor/                  # 근태, 인건비율
│  ├─ food_cost/              # 식재료비, 원가율
│  ├─ inventory/              # 육류 입출고, 폐기, 재고 실사 차이
│  ├─ customer/               # 평점, 리뷰, 클레임 VOC
│  ├─ management/             # 공헌이익, 경영 종합
│  ├─ rules.py                # 순수 비즈니스 룰 및 일반화 디텍터
│  └─ pipeline.py             # 92일 파이프라인 러너 (Partial Facts 지원)
├─ data/                      # 데이터 저장소
│  ├─ synthetic/              # V2 골든 데이터셋 및 가상 데이터
│  ├─ fixtures/               # Mock Fixture & 적대적 데이터셋
│  └─ damga_ops.db            # SQLite 프로덕션/개발 데이터베이스
├─ tests/                     # 7계층 테스트 스위트 (224 Tests Passed)
│  ├─ unit/                   # 단위 및 경계 돌연변이 테스트
│  ├─ integration/            # 파이프라인 통합 테스트
│  ├─ golden/                 # GA-001 ~ GA-007 골든 시나리오 및 적대적 일반화
│  ├─ storage/                # Storage 계층 및 Ingestion 테스트
│  ├─ api/                    # FastAPI 엔드포인트 테스트
│  ├─ analyst/                # AI Analyst, Provider Failures, Prompt Injection, Hash Chain
│  ├─ adapters/               # Source Adapters, Mapping Engine, Privacy, Quarantine, Reconciliation
│  ├─ migration/              # Non-Destructive Schema Migration Tests (MIG-01 ~ 04)
│  └─ persistence/            # DB 회귀 및 독립 DB 재현성 테스트
├─ scripts/                   # 빌드, 데이터 로더, 하네스 실행 스크립트
└─ evidence/                  # 실행 및 검증 증적(Evidence) 저장소
```

---

## 4. 실데이터 연동 및 섀도우 모드 (Real-Data Readiness & Shadow Mode)

### 4.1 Generic Source Adapter
- 벤더 독립적인 Generic CSV 및 Generic XLSX Adapter 구현.
- 원천 파일 프로파일링 (`SourceProfiler`), 컬럼명 및 데이터 타입 추론, 결측치/중복 행 산출.

### 4.2 매핑 및 격리 레이어 (Mapping & Quarantine)
- 한글/영문 이명 사전(`ALIAS_DICTIONARY`)을 통한 결정론적 매핑 제안.
- 매핑 매니페스트(`MappingManifest`)의 인간 검토 및 승인(`CONFIRMED`).
- 행 단위 유효성 검사 및 불량 데이터 격리(`QuarantineRecord`), 배치 중단 없이 유효 데이터 지속 처리.

### 4.3 PII 보호 (Sensitive Column Detector)
- 주민등록번호, 전화번호, 카드번호, 계좌번호, 고객명 등 민감 정보 감지 시 자동 임포트 차단(`BLOCKED`) 및 비식별 마스킹(`0***********8`).

### 4.4 데이터 대사 (Reconciliation Engine)
- 상세 거래 내역 합계 vs 일일 요약/세금계산서 청구액 간 오차 검증 (`MATCH`, `MINOR_MISMATCH`, `MAJOR_MISMATCH`, `NOT_COMPARABLE`).

### 4.5 섀도우 모드 (Shadow Mode Isolation)
- `dataset_type = 'SHADOW_REAL'` 격리 실행을 통해 기존 Synthetic Ground Truth를 보존하고 AI 운영 권고 자동 실행을 원천 차단.

---

## 5. 경영체계 프로토타입 (Phase 6)

Phase 6는 실제 사용 전 검증을 위해 `100% SYNTHETIC` 데이터로 다음 폐쇄 루프를 확장한다.

`Monthly Finance -> Menu Engineering -> Organization/RACI -> SOP -> Action Closure -> Monthly Review -> Human Approval -> Evidence`

- 결정론 엔진: `domains/management/prototype.py`
- API: `/api/v1/management/*`
- 저장: `management_actions`, `management_action_events`
- UI: `ManagementSystemSection`
- 브랜드: `담가화로구이`
- 미확정 정책: 비용 배부, 메뉴 ABCD 기준, 관리자 KPI 가중치는 `UNVERIFIED POLICY`
- 자동 가격변경·발주·지급·인사조치는 비활성화한다.



