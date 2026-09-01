# Real-Data Store Onboarding Guide v1.0

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
