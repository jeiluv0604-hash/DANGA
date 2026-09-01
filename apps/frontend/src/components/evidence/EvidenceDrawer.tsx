import React, { useEffect, useState } from 'react';
import { EvidenceDetail, EvidenceVerifyResult } from '../../types/evidence';
import { fetchEvidenceDetail, verifyEvidence } from '../../api/evidence';
import { truncateHash } from '../../utils/formatters';

interface EvidenceDrawerProps {
  evidenceId: string | null;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({ evidenceId, onClose }) => {
  const [detail, setDetail] = useState<EvidenceDetail | null>(null);
  const [verify, setVerify] = useState<EvidenceVerifyResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!evidenceId) return;
    setLoading(true);
    setError(null);
    Promise.all([fetchEvidenceDetail(evidenceId), verifyEvidence(evidenceId)])
      .then(([d, v]) => {
        setDetail(d);
        setVerify(v);
      })
      .catch((err: any) => {
        setError(err.message || '증적 정보를 불러오지 못했습니다.');
      })
      .finally(() => setLoading(false));
  }, [evidenceId]);

  if (!evidenceId) return null;

  return (
    <div
      data-testid="evidence-drawer"
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '100%',
        maxWidth: '460px',
        backgroundColor: '#0f172a',
        borderLeft: '1px solid #334155',
        boxShadow: '-4px 0 20px rgba(0,0,0,0.6)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid #1e293b',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold', color: '#f8fafc', margin: 0 }}>
            증적(Evidence) 무결성 검증
          </h3>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>ID: {evidenceId}</span>
        </div>
        <button
          onClick={onClose}
          aria-label="닫기"
          style={{
            padding: '4px 8px',
            backgroundColor: '#1e293b',
            color: '#cbd5e1',
            borderRadius: '4px',
            fontSize: '14px',
            fontWeight: 'bold',
          }}
        >
          ✕
        </button>
      </div>

      <div style={{ padding: '20px', overflowY: 'auto', flex: 1 }}>
        {loading ? (
          <div style={{ color: '#94a3b8', textAlign: 'center', padding: '40px 0' }}>
            증적 파일 암호화 검증 중...
          </div>
        ) : error ? (
          <div style={{ color: '#f87171', padding: '20px', backgroundColor: '#450a0a', borderRadius: '6px' }}>
            {error}
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>암호화 해시 검증 상태</div>
              {verify?.integrity === 'VALID' ? (
                <div
                  data-testid="evidence-status-valid"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    backgroundColor: '#064e3b',
                    border: '1px solid #10b981',
                    color: '#a7f3d0',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    fontSize: '14px',
                  }}
                >
                  <span>✓</span>
                  <span>무결성 검증됨 (VALID)</span>
                </div>
              ) : verify?.integrity === 'INVALID' ? (
                <div
                  data-testid="evidence-status-invalid"
                  style={{
                    backgroundColor: '#450a0a',
                    border: '1px solid #ef4444',
                    color: '#fecaca',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    fontSize: '14px',
                  }}
                >
                  <span>⚠</span>
                  <span>무결성 검증 실패 (INVALID - 파일 위변조 감지)</span>
                </div>
              ) : (
                <div
                  style={{
                    backgroundColor: '#431407',
                    border: '1px solid #f97316',
                    color: '#fed7aa',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    fontSize: '14px',
                  }}
                >
                  <span>?</span>
                  <span>증적 파일 없음 (MISSING_FILE)</span>
                </div>
              )}
            </div>

            <div style={{ backgroundColor: '#131b2e', borderRadius: '8px', padding: '14px', marginBottom: '20px' }}>
              <h4 style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '10px' }}>증적 메타데이터</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>발생 일자</span>
                  <span style={{ color: '#f8fafc', fontWeight: 'bold' }}>{detail?.business_date || '-'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>규칙 ID</span>
                  <span style={{ color: '#f8fafc', fontFamily: 'monospace' }}>{detail?.rule_id || '-'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>파일 경로</span>
                  <span style={{ color: '#94a3b8', fontFamily: 'monospace' }}>{detail?.file_path || '-'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Evidence SHA-256</span>
                  <span style={{ color: '#38bdf8', fontFamily: 'monospace' }} title={detail?.file_sha256}>
                    {truncateHash(detail?.file_sha256)}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Dataset SHA-256</span>
                  <span style={{ color: '#94a3b8', fontFamily: 'monospace' }} title={detail?.dataset_sha256}>
                    {truncateHash(detail?.dataset_sha256)}
                  </span>
                </div>
              </div>
            </div>

            <p style={{ fontSize: '11px', color: '#64748b', lineHeight: 1.4 }}>
              * 본 증적 검증은 디스크에 저장된 증적 파일 바이트로부터 SHA-256을 실시간 계산하여 원본 등록 해시와 100% 일치함을 보증합니다.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
