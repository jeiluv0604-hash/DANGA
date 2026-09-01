# 📋 DAMGA-OPS 프로젝트 개발 인수인계서 (Handover Guide)

> **문서 버전**: v1.1.0 (Phase 6 경영체계 프로토타입 완료 시점)  
> **대상 시스템**: 담가화로구이 외식업 통합 경영자동화 Cockpit (DAMGA-OPS)  
> **후속 작업자**: OpenAI Codex / 차기 AI 에이전트 및 백엔드/프론트엔드 엔지니어  
> **최상위 원칙**: `docs/product/master-specification-v1.0.md`, `AGENTS.md`, `docs/quality/golden-principles.md`

---

## 1. 프로젝트 개요 및 핵심 미션 (Mission & Rules)

### 1.1 프로젝트 미션
- **대상 매장**: 담가화로구이 (단일 매장, 연매출 42억원, 직원 풀 65명 기준)
- **핵심 목표**: POS(매출), 근태(인건비), 매입(식재료비), 재고(육류 실사), 고객(VOC) 데이터를 통합하여 **매일 3분 안에 경영 이상을 감지하고 의사결정을 지원하는 자동화 시스템**.
- **설계 철학 (Harness Engineering)**: "AI가 숫자를 만드는 시스템"이 아니라 **"100% 결정론적 계산 엔진(Facts Engine)이 산출한 사실을 AI가 경영 언어로 해석하는 시스템"**.

### 1.2 절대 금지 사항 (NEVER Rules)
1. **No Hallucinated Numbers (GP-01)**: LLM이 임의로 숫자를 계산/추정 금지. 모든 지표는 Facts Engine(Python/SQL)에서만 산출.
2. **No Data Forgery (GP-02)**: 필수 데이터 누락 시 추정치로 채우지 말고 `DATA_INCOMPLETE`로 안전 차단(Block).
3. **Missing != Zero (GP-03)**: 결측값(미입력)과 0(Zero)을 절대 혼동하지 말 것 (예: 서비스량 미기록 시 `None` 유지, 0 처리 금지).
4. **No Unauthorized Execution (GP-04)**: 인력 감원, 가격 변경, 발주 변경 등 경영 조치를 사람의 승인 없이 자동 실행 금지.
5. **No Accusations (GP-05)**: 재고 차이를 절도/횡령으로 단정하지 말고 확인 대상 이상(Anomaly)으로만 기술.
6. **No DB Drop (Safety)**: Phase 5부터 `Base.metadata.drop_all()` 금지. 비파괴적 Alembic 마이그레이션만 사용.

---

## 2. 완료된 Phase별 구현 내역 (Completed Work: Phase 1 ~ Phase 5)

| Phase | 주요 구현 내용 | 검증 결과 |
|---|---|---|
| **Phase 1** | **Deterministic Facts & Rule Engine**: 6대 핵심 KPI 계산기, 7대 Golden Anomaly 탐지기 (GA-001~007), Golden Harness. | PASS |
| **Phase 1.1** | **Adversarial Validation**: 날짜/정답 컬럼 변경 시에도 이상을 탐지하는 일반화 룰 엔진 검증 (Zero Test Leakage). | PASS |
| **Phase 2** | **API & Storage Foundation**: FastAPI REST API, SQLite ORM 저장소, Synthetic 데이터 적재 파이프라인, Evidence 파일 저장. | PASS |
| **Phase 2.1** | **Data Semantics & Evidence Linkage**: Partial Facts (부분 결측 시 유효 지표 보존), Alert-Evidence 1:1 바인딩, Structured Logging. | PASS |
| **Phase 2.2** | **Cryptographic Integrity & Missing Semantics**: Evidence 파일의 실제 바이트 SHA-256 해시 인덱스 검증, Missing!=Zero 엄격 적용. | PASS |
| **Phase 3** | **CEO Cockpit Web Dashboard**: React 18 + Vite + TypeScript + TailwindCSS + Recharts 대시보드, 6대 KPI 카드, 7일 추세 차트, 증적 서랍. | PASS |
| **Phase 4** | **AI Analyst & Human-in-the-Loop**: Facts 기반 일일 브리핑, 원인 가설, 휴먼 승인/반려 시뮬레이션 워크플로우, Decision Action 저장. | PASS |
| **Phase 4.1** | **AI Grounding & Safety Hardening**: Semantic FactRef 바인딩, Provider 장애 시 명시적 실패(`PROVIDER_UNAVAILABLE`), 해시 체인 감사 로그. | PASS |
| **Phase 5** | **Real-Data Readiness & Shadow Mode**: Generic CSV/XLSX 어댑터, 4대 도메인 Canonical 스키마, 매핑 매니페스트, 격리 레이어(Quarantine), PII 보호(Sensitive Column Detector), 대사(Reconciliation) 엔진, Alembic 마이그레이션. | PASS |
| **Phase 6** | **담가화로구이 Management System Prototype**: 6개월 Synthetic 재무, 일일 10 KPI, 월 손익, Budget vs Actual, Cash Flow, Recipe/BOM, 메뉴 ABCD, 조직/RACI, 관리자 Scorecard, 전결정책, SOP/Checklist, Action Closure, 월간 경영회의 및 Management Brief. | PASS |

---

## 3. 시스템 아키텍처 및 디렉터리 맵 (Architecture & Map)

```
c:\Users\a\damga/
├── AGENTS.md                  # 에이전트 작업 헌장 및 규칙
├── ARCHITECTURE.md            # 시스템 계층 및 아키텍처 정의서
├── HANDOVER.md                # 🌟 본 인수인계 문서
├── alembic.ini                # Alembic DB 마이그레이션 설정
├── migrations/                # Alembic 마이그레이션 스크립트
├── mappings/                  # 4대 도메인 표준 매핑 매니페스트 (JSON)
├── fixtures/source_samples/   # 실무 형태의 원천 CSV/XLSX 샘플 데이터셋
├── data/
│   ├── damga_ops.db           # SQLite 메인 데이터베이스
│   └── synthetic/             # Golden Dataset (V2)
├── domains/                   # 100% 순수 결정론적 도메인 로직
│   ├── adapters/              # CSV/XLSX 어댑터, 프로파일링, 매핑, 격리, 대사, 섀도우
│   ├── data_quality/          # Data Quality Gate & 스키마 검증
│   ├── sales/                 # 매출, 객수, 객단가
│   ├── labor/                 # 근태, 인건비율
│   ├── food_cost/             # 식재료비, 원가율
│   ├── inventory/             # 육류 입출고, 재고 실사 차이
│   ├── customer/              # 평점, 리뷰, 클레임 VOC
│   ├── analyst/               # AI Analyst Context Builder, Safety, Providers
│   ├── rules.py               # 7대 이상 탐지 룰 엔진
│   └── pipeline.py            # 파이프라인 러너 (Partial Facts 지원)
├── apps/
│   ├── api/                   # FastAPI 백엔드
│   │   ├── config.py          # 환경변수 및 DB URL (sqlite:///data/damga_ops.db)
│   │   ├── database.py        # SQLAlchemy 엔진 및 세션
│   │   ├── models/            # ORM 모델 (facts, alerts, analyst, canonical, imports 등)
│   │   ├── repositories/      # DB 접근 계층
│   │   ├── services/          # 비즈니스 서비스 계층
│   │   └── routes/            # REST API 라우터 (/dashboard, /analyst, /imports 등)
│   └── frontend/              # React 18 + Vite + TypeScript 대시보드
│       ├── src/components/    # kpi, alerts, charts, analyst, evidence, shadow badge
│       ├── src/hooks/         # useDailyDashboard, useRecentTrends, useAnalystBrief 등
│       └── vite.config.ts     # Vite 설정 (Host: 0.0.0.0, Port: 3000, Proxy: 8000)
├── tests/                     # 244개 자동화 테스트 스위트
│   ├── unit/                  # 단위 및 경계값 테스트
│   ├── golden/                # GA-001 ~ GA-007 골든 시나리오 테스트
│   ├── storage/               # Evidence 해시 무결성 및 DB 저장 테스트
│   ├── api/                   # REST API 엔드포인트 테스트
│   ├── analyst/               # AI Analyst, Provider Failure, Hash Chain 테스트
│   ├── adapters/              # Source Adapters, Mapping, Quarantine, Reconciliation 테스트
│   └── migration/             # Non-destructive Alembic 마이그레이션 테스트
└── evidence/                  # 실행 증적 JSON 및 SHA-256 인덱스 저장소
```

---

## 4. 데이터베이스 및 스키마 현황 (Database & Migrations)

- **DB 파일 경로**: `data/damga_ops.db`
- **ORM**: SQLAlchemy 2.x (`Base = declarative_base()`)
- **마이그레이션 관리**: Alembic (`alembic upgrade head`)
- **주요 테이블 목록**:
  - 기존: `daily_operations`, `daily_facts`, `alerts`, `period_alerts`, `ingestion_runs`, `evidence_index`, `analyst_briefs`, `decision_actions`, `decision_audit_logs`
  - Phase 5 추가: `source_imports`, `quarantine_records`, `mapping_manifests`, `canonical_pos_transactions`, `canonical_attendance_records`, `canonical_purchase_records`, `canonical_inventory_records`
  - 공통 추가 컬럼: `verification_status` (`UNVERIFIED`, `MAPPED`, `VALIDATED`, `RECONCILED`, `APPROVED`)

---

## 5. 실행 및 검증 가이드 (How to Run & Verify)

### 5.1 서버 구동
```powershell
# 1. 백엔드 API 서버 (Port 8000)
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

# 2. 프론트엔드 Vite 개발 서버 (Port 3000)
cd apps/frontend
npm run dev
```

### 5.2 전체 테스트 스위트 실행 (총 244개 테스트 100% PASS 검증)
```powershell
# 1. 백엔드/도메인/어댑터/마이그레이션 테스트 (202 tests)
python -m pytest tests/ -v

# 2. 프론트엔드 유닛/컴포넌트 테스트 (24 tests)
cd apps/frontend
cmd /c "npm run test"

# 3. 프론트엔드 E2E 브라우저 테스트 (18 tests)
cd apps/frontend
cmd /c "npm run test:e2e"
```

---

## 6. 코덱스(Codex) / 후속 에이전트를 위한 핵심 지침 (Instructions for Codex)

1. **결정론적 로직 우선 (Deterministic First)**:
   - 새로운 지표나 계산이 필요할 경우, LLM 프롬프트에 넣지 말고 반드시 `domains/` 내에 순수 Python 함수로 작성하고 단위 테스트를 추가하십시오.
2. **DB 스키마 변경 시 주의사항**:
   - 기존 데이터를 파괴하는 `drop_all()`을 절대 호출하지 마십시오. 스키마 변경이 필요한 경우 `alembic revision` 스크립트를 작성하여 적용하십시오.
3. **실데이터(Real Data) 취급 원칙**:
   - 실데이터 파일 유입 시 `dataset_type = 'SHADOW_REAL'` 모드로 격리 임포트하고, 대사(`ReconciliationEngine`) 검증 및 관리자 승인 전까지 프로덕션 진실 지표를 덮어쓰지 마십시오.
4. **증적 시스템 연동**:
   - 새로운 룰이나 알림 추가 시 `evidence_id`를 생성하고 `evidence_index` 테이블 및 `evidence/` 파일 저장소와 연동하십시오.

---

## 7. Phase 6 경영체계 프로토타입

- 브랜드명: `담가화로구이`
- 목적: 실제 사용 전 검증용 프로토타입
- 데이터: `SYNTHETIC · 실제 담가화로구이 매장 데이터 아님`
- API 버전: `6.0.0-prototype`
- 엔진: `domains/management/prototype.py`
- API: `/api/v1/management/*`
- UI: `apps/frontend/src/components/management/ManagementSystemSection.tsx`
- 마이그레이션: `c6f9a1b2d3e4 (head)`

다음 세 정책은 사용자 지시에 따라 실제 승인 전까지 `UNVERIFIED POLICY`다.

1. 월 손익 비용 계정·부문별 배부 기준
2. 메뉴 ABCD 판정 기준
3. 관리자 KPI 가중치

자동 가격 변경, 자동 발주·지급, 자동 인사평가·승진·보상·징계·해고는 비활성화되어 있다. Action 상태변경은 Human Approval과 SHA-256 감사 이벤트를 남긴다.

### Phase 6 검증 결과

- Pytest: `202 PASS`
- Vitest: `24 PASS`
- Playwright: `18 PASS` (Chromium + Tablet)
- Production build: `PASS`
- 합계: `244 PASS / 0 failures`
- Live API: `http://127.0.0.1:8000`, version `6.0.0-prototype`
- Frontend: `http://127.0.0.1:3000`
- Visual Evidence: `evidence/EV-UI-MANAGEMENT-PROTOTYPE.png`

### 재현 가능한 설정

```powershell
.\bootstrap.ps1
```

Bootstrap은 `.venv` 생성, 고정 버전 의존성 설치, Alembic upgrade, Pytest, Vitest, production build를 순서대로 수행한다.
