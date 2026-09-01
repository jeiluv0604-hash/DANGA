# Real-Data Privacy & Security Specification v1.0

## 1. PII 차단 원칙
1. **No Personal Names in Attendance**: 직원 근태 데이터에는 실명을 저장하지 않고 비식별 사번(`employee_id`)만 사용합니다.
2. **Sensitive Columns Detection**: 주민번호, 전화번호, 카드번호, 계좌번호, 이메일 등이 포함된 컬럼 헤더 감지 시 즉시 `SENSITIVE_COLUMN_DETECTED`로 격리 및 임포트 차단(`BLOCKED`).
3. **Safe Sample Masking**: 데이터 프로파일링 시 미리보기 값은 `0***********8` 형식으로 비식별 마스킹됩니다.
4. **Quarantine Row Security**: 격리 레코드에는 원천 PII가 원문 그대로 남지 않도록 안전 미리보기(Safe Value Preview)만 기록합니다.
