# Human Decision Audit Trail & Tamper-Evident Hash Chain Specification v1.1

## 1. 개요
경영자의 의사결정(승인/반려) 이력을 추적하고 위변조를 방지하기 위해 Application-Level Append-Only Audit Log 및 Tamper-Evident Hash Chain을 구현합니다.

## 2. 상태 전이 머신 (State Machine)
- REVIEW_REQUIRED -> APPROVED (허용)
- REVIEW_REQUIRED -> REJECTED (허용)
- APPROVED -> APPROVED (차단: 409 Conflict)
- APPROVED -> REJECTED (차단: 409 Conflict)
- REJECTED -> APPROVED (차단: 409 Conflict)
- REJECTED -> REJECTED (차단: 409 Conflict)

## 3. Tamper-Evident Hash Chain
- previous_hash: 최초 이벤트는 GENESIS, 이후 직전 로그의 event_hash
- canonical_str: {previous_hash}|{brief_id}|{action_type}|{actor_role}|{timestamp}|{comment}
- event_hash: SHA256(canonical_str)
- **정확한 용어**: 'application-level append-only audit log', 'tamper-evident hash chain' (암호학적 완전 불변성 또는 블록체인이 아닌 애플리케이션 무결성 보장).
