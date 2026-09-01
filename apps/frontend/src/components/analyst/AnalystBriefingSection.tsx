import React, { useState } from 'react';
import { AlertTriangle, Bot, CheckCircle2, ShieldCheck, XCircle } from 'lucide-react';

import { useAnalystBrief } from '../../hooks/useAnalystBrief';

interface AnalystBriefingSectionProps {
  date: string;
  onOpenEvidence: (evidenceId: string) => void;
}

const card: React.CSSProperties = { background: '#131b2e', border: '1px solid #23314e', borderRadius: '12px', padding: '14px' };
const actionButton: React.CSSProperties = { display: 'inline-flex', alignItems: 'center', gap: '5px', borderRadius: '8px', padding: '8px 13px', color: '#fff', fontSize: '12px', fontWeight: 700 };

export const AnalystBriefingSection: React.FC<AnalystBriefingSectionProps> = ({ date, onOpenEvidence }) => {
  const { brief, loading, actionLoading, error, handleApprove, handleReject } = useAnalystBrief(date);
  const [reviewerRole, setReviewerRole] = useState<'CEO' | 'GENERAL_MANAGER'>('CEO');
  const [commentText, setCommentText] = useState('');

  if (loading) return <section style={{ ...card, marginBottom: '28px', color: '#94a3b8' }}>AI 경영분석을 준비하는 중입니다.</section>;
  if (error || !brief) return null;

  const isBlocked = brief.status === 'BLOCKED';
  const isApproved = brief.status === 'APPROVED';
  const isRejected = brief.status === 'REJECTED';
  const statusLabel = isBlocked ? '분석 차단' : isApproved ? '승인 완료' : isRejected ? '반려' : '검토 대기';

  return (
    <section aria-label="AI 경영분석 및 의사결정 지원" data-testid="compact-ai-briefing" style={{ marginBottom: '28px' }}>
      <div style={{ background: 'linear-gradient(135deg, #111827 0%, #172554 100%)', border: '1px solid #3730a3', borderRadius: '16px', padding: '20px', boxShadow: '0 12px 28px rgba(0,0,0,.25)' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px', paddingBottom: '13px', borderBottom: '1px solid #3730a3' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '11px' }}>
            <span style={{ display: 'grid', placeItems: 'center', width: '38px', height: '38px', borderRadius: '11px', background: '#312e81', color: '#c7d2fe' }}><Bot size={21} /></span>
            <div><h2 style={{ fontSize: '17px', margin: 0 }}>AI 경영분석 및 의사결정 지원</h2><p style={{ margin: '3px 0 0', color: '#94a3b8', fontSize: '12px' }}>핵심 이상과 우선 조치만 요약 · 사람 승인 후 현장 반영</p></div>
          </div>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', borderRadius: '999px', padding: '5px 10px', fontSize: '11px', fontWeight: 800, color: isBlocked ? '#fecaca' : '#c7d2fe', background: isBlocked ? '#7f1d1d' : '#312e81', border: `1px solid ${isBlocked ? '#dc2626' : '#4f46e5'}` }}>{isBlocked && <AlertTriangle size={13} />}{statusLabel}</span>
        </div>

        <div style={{ marginTop: '11px', padding: '7px 10px', borderRadius: '8px', color: '#fde68a', background: 'rgba(180,83,9,.22)', border: '1px solid rgba(245,158,11,.3)', fontSize: '11px' }}>{brief.dataset_type} · 실제 매장 데이터가 아닌 가상 데이터 분석</div>

        <div style={{ ...card, marginTop: '12px', background: 'rgba(15,23,42,.72)' }}><h3 style={{ color: '#94a3b8', fontSize: '11px', marginBottom: '5px' }}>오늘의 결론</h3><p style={{ color: '#f8fafc', fontSize: '13px', fontWeight: 600, lineHeight: 1.65 }}>{brief.executive_summary}</p></div>

        {!isBlocked && <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', marginTop: '12px' }}>
          <div style={{ ...card, background: 'rgba(15,23,42,.55)' }}><h3 style={{ color: '#fca5a5', fontSize: '12px', marginBottom: '9px' }}>핵심 이상</h3><ol style={{ paddingLeft: '18px', color: '#cbd5e1', fontSize: '12px' }}>{brief.findings.slice(0, 3).map((finding, index) => <li key={`${finding.rule_id}-${index}`} style={{ marginBottom: '7px' }}><button onClick={() => finding.evidence_ids[0] && onOpenEvidence(finding.evidence_ids[0])} style={{ color: '#cbd5e1', textAlign: 'left', lineHeight: 1.5 }}>{finding.finding}</button></li>)}</ol></div>
          <div style={{ ...card, background: 'rgba(15,23,42,.55)' }}><h3 style={{ color: '#6ee7b7', fontSize: '12px', marginBottom: '9px' }}>우선 조치</h3><ol style={{ paddingLeft: '18px', color: '#cbd5e1', fontSize: '12px' }}>{brief.recommended_actions.slice(0, 3).map((action, index) => <li key={`${action.action}-${index}`} style={{ marginBottom: '7px', lineHeight: 1.5 }}>{action.action}<span style={{ color: '#64748b' }}> · {action.owner_role}</span></li>)}</ol></div>
        </div>}

        {!isBlocked && <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '10px', marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #334155' }}>
          <div style={{ display: 'flex', flex: '1 1 350px', gap: '8px' }}>
            <select aria-label="검토자" value={reviewerRole} onChange={(event) => setReviewerRole(event.target.value as 'CEO' | 'GENERAL_MANAGER')} disabled={actionLoading} style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px', padding: '7px 9px', color: '#e2e8f0', fontSize: '12px' }}><option value="CEO">대표</option><option value="GENERAL_MANAGER">총괄점장</option></select>
            <input value={commentText} onChange={(event) => setCommentText(event.target.value)} placeholder="결정 의견 입력 (선택)" disabled={actionLoading} style={{ flex: 1, minWidth: 0, background: '#0f172a', border: '1px solid #334155', borderRadius: '8px', padding: '7px 10px', color: '#e2e8f0', fontSize: '12px' }} />
          </div>
          <div style={{ display: 'flex', gap: '7px' }}><button onClick={() => handleReject(reviewerRole, commentText)} disabled={actionLoading || isRejected} style={{ ...actionButton, background: '#7f1d1d', opacity: actionLoading || isRejected ? .5 : 1 }}><XCircle size={14} />반려</button><button onClick={() => handleApprove(reviewerRole, commentText)} disabled={actionLoading || isApproved} style={{ ...actionButton, background: '#4f46e5', opacity: actionLoading || isApproved ? .5 : 1 }}><CheckCircle2 size={14} />승인</button></div>
        </div>}
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginTop: '9px', color: '#64748b', fontSize: '10px' }}><ShieldCheck size={12} />AI 자동 실행 금지 · 최종 결정은 사용자 책임</div>
      </div>
    </section>
  );
};
