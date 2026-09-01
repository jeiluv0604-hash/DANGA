# -*- coding: utf-8 -*-
import os

doc_files = {
    "docs/data/source-adapter-contract-v1.0.md": """# Source Adapter Contract Specification v1.0

## 1. Adapter 아키텍처 원칙
1. **Generic-First**: 특정 벤더(OKPOS, EasyPOS 등) 하드코딩 금지. Generic CSV Adapter 및 Generic XLSX Adapter 기반으로 확장.
2. **Deterministic Transformation**: 원천 컬럼 파싱과 정규화는 결정론적 매핑 매니페스트에 의해 수행.
3. **Quarantine Isolation**: 개별 레코드의 결함(날짜 오류, 음수 매출, 중복)이 전체 배치를 실패시키지 않고 격리(Quarantine).
4. **Zero Accusations & Privacy**: PII 검출 시 수입 차단 및 안전 마스킹.

## 2. 인터페이스 명세
- `detect_source_type(file_path)` -> `POS | ATTENDANCE | PURCHASE | INVENTORY | UNKNOWN`
- `profile(file_path, sheet_name)` -> `DataProfile`
- `map_to_canonical(file_path, manifest, sheet_name)` -> `MappingResult`
""",

    "docs/data/mapping-manifest-v1.0.md": """# Mapping Manifest Specification v1.0

## 1. 구조 (Schema)
매핑 매니페스트는 원천 컬럼 헤더와 Canonical 표준 필드 간의 1:1 대응 규칙을 정의합니다.
- `mapping_id`: 매핑 고유 식별자 (예: MAP-POS-GENERIC-V1)
- `source_type`: 대상 도메인 (POS, ATTENDANCE, PURCHASE, INVENTORY)
- `mapping_version`: 매핑 버전 (시맨틱 버저닝 1.0.0)
- `status`: SUGGESTED | CONFIRMED | REJECTED
- `column_mappings`: 원천컬럼명 -> 표준필드명 딕셔너리
- `transforms`: 선택적 정규화 규칙
- `confirmed_by`: 승인자 역할/아이디
- `confirmed_at`: 승인 시각

## 2. 관리 원칙
1. AI/휴리스틱 매핑 제안은 `SUGGESTED` 상태로 생성되며, 사람의 검토 후 `CONFIRMED` 상태로 승인되어야 운영에 적용됩니다.
2. 매핑 버전이 변경되면 이전 버전과의 차이 및 데이터 계통이 감사 로그에 기록됩니다.
""",

    "docs/data/reconciliation-contract-v1.0.md": """# Data Reconciliation Contract Specification v1.0

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
""",

    "docs/data/shadow-mode-v1.0.md": """# Shadow Mode Architecture Specification v1.0

## 1. 목적 (Mission)
실제 매장 데이터를 수신하더라도 기존 검증된 Synthetic Ground Truth 파이프라인을 손상시키지 않고 병렬로 검증(Shadowing)합니다.

## 2. 핵심 통제 규칙
1. **No Truth Overwrite**: `dataset_type = 'SHADOW_REAL'` 데이터는 CEO Dashboard의 기존 공인 진실 데이터를 덮어쓰지 않습니다.
2. **AI Action Blocking**: Shadow Mode 데이터에서는 AI Analyst의 운영 변경 조치 권고가 비활성화됩니다 (`ai_eligible = False`).
3. **Synthetic Calibration Badge**: UI 및 리포트에 `SHADOW REAL - 실제 데이터 검증 중 · 운영 판단용 아님` 뱃지가 강제 표시됩니다.
4. **Reconciliation Gate**: Shadow 데이터가 완전히 MAPPED 및 RECONCILED 검증을 거치기 전에는 `UNVERIFIED` 상태를 유지합니다.
""",

    "docs/security/real-data-privacy-v1.0.md": """# Real-Data Privacy & Security Specification v1.0

## 1. PII 차단 원칙
1. **No Personal Names in Attendance**: 직원 근태 데이터에는 실명을 저장하지 않고 비식별 사번(`employee_id`)만 사용합니다.
2. **Sensitive Columns Detection**: 주민번호, 전화번호, 카드번호, 계좌번호, 이메일 등이 포함된 컬럼 헤더 감지 시 즉시 `SENSITIVE_COLUMN_DETECTED`로 격리 및 임포트 차단(`BLOCKED`).
3. **Safe Sample Masking**: 데이터 프로파일링 시 미리보기 값은 `0***********8` 형식으로 비식별 마스킹됩니다.
4. **Quarantine Row Security**: 격리 레코드에는 원천 PII가 원문 그대로 남지 않도록 안전 미리보기(Safe Value Preview)만 기록합니다.
""",

    "docs/operations/real-data-onboarding-v1.0.md": """# Real-Data Store Onboarding Guide v1.0

## 매장 데이터 온보딩 6단계 절차

1. **Step 1: Source File Profile**
   - 매장 POS/근태/매입 엑셀/CSV 업로드
   - `POST /api/v1/imports/profile` 실행하여 컬럼, 행수, 결측치, PII 검출 여부 확인

2. **Step 2: Mapping Suggestion & Human Review**
   - `POST /api/v1/imports/map`으로 Canonical 필드 매핑 제안 확인
   - 담당자 검토 후 `POST /api/v1/mappings/confirm`으로 매핑 매니페스트 승인

3. **Step 3: Pre-Ingestion Validation & Quarantine Check**
   - `POST /api/v1/imports/validate`로 포맷 검증 및 격리 건수 확인

4. **Step 4: Shadow Mode Ingestion**
   - `POST /api/v1/imports/ingest-shadow` 실행
   - SHADOW_REAL 모드로 Canonical DB 저장 및 대사 리포트 생성

5. **Step 5: Reconciliation & Quality Verification**
   - `GET /api/v1/imports/{import_id}/reconciliation` 및 `/quality` 확인
   - 일치 상태(`MATCH`) 및 Readiness(`SHADOW_READY`) 검증

6. **Step 6: CEO Truth Promotion (승인 후 적용)**
   - 대사 결과가 완벽하고 Human Review가 완료된 경우에 한하여 `APPROVED` 및 Truth 승격
"""
}

for path, content in doc_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {path}")

print("All Phase 5 docs written successfully.")

