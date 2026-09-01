# Mapping Manifest Specification v1.0

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
