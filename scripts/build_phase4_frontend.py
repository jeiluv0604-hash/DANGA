# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print('Wrote:', path)

# 1. Types
write_file('apps/frontend/src/types/analyst.ts', """export interface FindingItem {
  finding: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  rule_id?: string;
  evidence_ids: string[];
}

export interface PossibleCauseItem {
  hypothesis: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  basis: string;
  evidence_ids: string[];
}

export interface RecommendedActionItem {
  action: string;
  owner_role: 'CEO' | 'GENERAL_MANAGER' | 'FLOOR_MANAGER' | 'KITCHEN_LEAD';
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  approval_required: boolean;
  evidence_ids: string[];
}

export interface DecisionAuditLogItem {
  log_id: string;
  brief_id: string;
  decision_id?: string;
  previous_status: string;
  new_status: string;
  actor_role: string;
  action_type: string;
  timestamp: string;
  comment?: string;
}

export interface AnalystBriefResponse {
  brief_id: string;
  business_date: string;
  dataset_type: string;
  status: 'READY' | 'BLOCKED' | 'REVIEW_REQUIRED' | 'APPROVED' | 'REJECTED';
  provider: string;
  model: string;
  prompt_version: string;
  facts_version: string;
  rule_version: string;
  executive_summary: string;
  findings: FindingItem[];
  possible_causes: PossibleCauseItem[];
  recommended_actions: RecommendedActionItem[];
  unknowns: string[];
  evidence_ids: string[];
  rejection_reasons: string[];
  created_at: string;
  reviewed_at?: string;
  approval_disclaimer: string;
}
""")

# 2. API
write_file('apps/frontend/src/api/analyst.ts', """import { apiFetch } from './client';
import { AnalystBriefResponse, DecisionAuditLogItem } from '../types/analyst';

export async function fetchDailyAnalystBrief(date: string): Promise<AnalystBriefResponse> {
  return apiFetch<AnalystBriefResponse>(`/analyst/daily/${date}`);
}

export async function approveAnalystBrief(
  briefId: string,
  reviewerRole: 'CEO' | 'GENERAL_MANAGER' = 'CEO',
  comment?: string
): Promise<AnalystBriefResponse> {
  return apiFetch<AnalystBriefResponse>(`/analyst/briefs/${briefId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ reviewer_role: reviewerRole, comment }),
  });
}

export async function rejectAnalystBrief(
  briefId: string,
  reviewerRole: 'CEO' | 'GENERAL_MANAGER' = 'CEO',
  comment?: string
): Promise<AnalystBriefResponse> {
  return apiFetch<AnalystBriefResponse>(`/analyst/briefs/${briefId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reviewer_role: reviewerRole, comment }),
  });
}

export async function fetchBriefAuditTrail(briefId: string): Promise<DecisionAuditLogItem[]> {
  return apiFetch<DecisionAuditLogItem[]>(`/analyst/briefs/${briefId}/audit`);
}
""")

# 3. Hook
write_file('apps/frontend/src/hooks/useAnalystBrief.ts', """import { useState, useEffect, useCallback } from 'react';
import { AnalystBriefResponse, DecisionAuditLogItem } from '../types/analyst';
import { fetchDailyAnalystBrief, approveAnalystBrief, rejectAnalystBrief, fetchBriefAuditTrail } from '../api/analyst';

export function useAnalystBrief(date: string) {
  const [brief, setBrief] = useState<AnalystBriefResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<DecisionAuditLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadBrief = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchDailyAnalystBrief(date);
      setBrief(data);
      if (data.brief_id) {
        const logs = await fetchBriefAuditTrail(data.brief_id);
        setAuditLogs(logs);
      }
    } catch (err: any) {
      setError(err.message || '경영 분석 브리핑을 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, [date]);

  useEffect(() => {
    loadBrief();
  }, [loadBrief]);

  const handleApprove = async (reviewerRole: 'CEO' | 'GENERAL_MANAGER' = 'CEO', comment?: string) => {
    if (!brief) return;
    try {
      setActionLoading(true);
      const updated = await approveAnalystBrief(brief.brief_id, reviewerRole, comment);
      setBrief(updated);
      const logs = await fetchBriefAuditTrail(brief.brief_id);
      setAuditLogs(logs);
    } catch (err: any) {
      setError(err.message || '승인 처리에 실패했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (reviewerRole: 'CEO' | 'GENERAL_MANAGER' = 'CEO', comment?: string) => {
    if (!brief) return;
    try {
      setActionLoading(true);
      const updated = await rejectAnalystBrief(brief.brief_id, reviewerRole, comment);
      setBrief(updated);
      const logs = await fetchBriefAuditTrail(brief.brief_id);
      setAuditLogs(logs);
    } catch (err: any) {
      setError(err.message || '반려 처리에 실패했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  return {
    brief,
    auditLogs,
    loading,
    actionLoading,
    error,
    refresh: loadBrief,
    handleApprove,
    handleReject,
  };
}
""")

# 4. Component
write_file('apps/frontend/src/components/analyst/AnalystBriefingSection.tsx', """import React, { useState } from 'react';
import { useAnalystBrief } from '../../hooks/useAnalystBrief';
import { Bot, ShieldCheck, CheckCircle2, XCircle, AlertTriangle, FileText, ChevronDown, ChevronUp, History } from 'lucide-react';

interface AnalystBriefingSectionProps {
  date: string;
  onOpenEvidence: (evidenceId: string) => void;
}

export const AnalystBriefingSection: React.FC<AnalystBriefingSectionProps> = ({
  date,
  onOpenEvidence,
}) => {
  const { brief, auditLogs, loading, actionLoading, error, handleApprove, handleReject } = useAnalystBrief(date);
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [showAuditModal, setShowAuditModal] = useState<boolean>(false);
  const [commentText, setCommentText] = useState<string>('');
  const [reviewerRole, setReviewerRole] = useState<'CEO' | 'GENERAL_MANAGER'>('CEO');

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm animate-pulse mb-8">
        <div className="h-6 bg-slate-200 rounded w-1/4 mb-4"></div>
        <div className="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-slate-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (error || !brief) {
    return null;
  }

  const isBlocked = brief.status === 'BLOCKED';
  const isApproved = brief.status === 'APPROVED';
  const isRejected = brief.status === 'REJECTED';

  const getStatusBadge = () => {
    if (isBlocked) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200">
          <AlertTriangle className="w-3.5 h-3.5" /> AI 분석 차단 (DATA_INCOMPLETE)
        </span>
      );
    }
    if (isApproved) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5" /> 경영진 승인 완료 (APPROVED)
        </span>
      );
    }
    if (isRejected) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
          <XCircle className="w-3.5 h-3.5" /> 경영진 반려 (REJECTED)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
        <ShieldCheck className="w-3.5 h-3.5" /> 경영진 검토 대기 (REVIEW REQUIRED)
      </span>
    );
  };

  return (
    <section aria-label="경영 분석 브리핑" className="mb-8">
      <div className="bg-gradient-to-br from-slate-900 to-indigo-950 text-white rounded-2xl p-6 shadow-xl border border-indigo-800/40">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-indigo-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-600/30 border border-indigo-500/40 rounded-xl text-indigo-300">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold tracking-tight">AI 경영 분석 브리핑 & 의사결정 지원</h2>
                <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-800/60 text-indigo-200 border border-indigo-700/50 font-mono">
                  {brief.model}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                결정론적 Facts Engine 기반 분석 • 원인 추정 및 조치 제안 (Human Approval Mandatory)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {getStatusBadge()}
            {auditLogs.length > 0 && (
              <button
                onClick={() => setShowAuditModal(true)}
                className="p-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 rounded-lg text-xs flex items-center gap-1 border border-slate-700 transition"
                title="감사 이력 확인"
              >
                <History className="w-3.5 h-3.5" /> 이력 ({auditLogs.length})
              </button>
            )}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 rounded-lg transition border border-slate-700"
              aria-label="브리핑 접기/펼치기"
            >
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Synthetic Data Warning */}
        <div className="mt-3 px-3 py-1.5 bg-amber-500/10 border border-amber-500/20 rounded-lg text-[11px] text-amber-300 flex items-center justify-between">
          <span>⚠️ {brief.dataset_type} DATASET: 실제 매장 데이터가 아닌 합성 데이터 기반 분석입니다.</span>
          <span className="text-slate-400 font-mono text-[10px]">{brief.prompt_version} / {brief.facts_version}</span>
        </div>

        {isExpanded && (
          <div className="mt-5 space-y-6">
            {/* Executive Summary */}
            <div className="p-4 bg-slate-800/60 rounded-xl border border-slate-700/50">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Executive Summary</h3>
              <p className="text-sm text-slate-100 leading-relaxed font-medium">
                {brief.executive_summary}
              </p>
            </div>

            {!isBlocked && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Findings & Evidence */}
                <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/40 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5" /> 핵심 이상 탐지 (Facts Grounded)
                    </h3>
                    <ul className="space-y-2.5">
                      {brief.findings.map((f, idx) => (
                        <li key={idx} className="text-xs text-slate-200 bg-slate-900/50 p-2.5 rounded-lg border border-slate-800">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-slate-300">#{idx + 1} {f.rule_id || 'FACT'}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                              f.severity === 'CRITICAL' ? 'bg-rose-900/60 text-rose-300' :
                              f.severity === 'HIGH' ? 'bg-amber-900/60 text-amber-300' : 'bg-slate-800 text-slate-400'
                            }`}>
                              {f.severity}
                            </span>
                          </div>
                          <p className="text-slate-300 mb-2">{f.finding}</p>
                          <div className="flex flex-wrap gap-1">
                            {f.evidence_ids.map(eid => (
                              <button
                                key={eid}
                                onClick={() => onOpenEvidence(eid)}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-indigo-900/40 hover:bg-indigo-800/60 border border-indigo-700/40 rounded text-[10px] text-indigo-300 font-mono transition"
                              >
                                🔗 {eid}
                              </button>
                            ))}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Possible Causes & Hypotheses */}
                <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/40 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs font-semibold text-emerald-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                      <Bot className="w-3.5 h-3.5" /> 원인 가설 및 점검 대상 (Non-accusing)
                    </h3>
                    <ul className="space-y-2.5">
                      {brief.possible_causes.map((c, idx) => (
                        <li key={idx} className="text-xs text-slate-200 bg-slate-900/50 p-2.5 rounded-lg border border-slate-800">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-slate-300">가설 #{idx + 1}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                              신뢰도: {c.confidence}
                            </span>
                          </div>
                          <p className="text-slate-200 font-medium mb-1">{c.hypothesis}</p>
                          <p className="text-[11px] text-slate-400">근거: {c.basis}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Recommended Actions & Human Decision Box */}
            {!isBlocked && (
              <div className="p-4 bg-slate-800/80 rounded-xl border border-indigo-700/40">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-semibold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4" /> 권고 조치 및 경영진 결재 (Human Approval)
                  </h3>
                  <span className="text-[11px] text-slate-400">
                    * AI 자동 실행 금지 — 사람의 승인 후에만 현장 반영
                  </span>
                </div>

                <div className="space-y-3 mb-4">
                  {brief.recommended_actions.map((act, idx) => (
                    <div key={idx} className="p-3 bg-slate-900/70 rounded-lg border border-slate-800 flex items-center justify-between gap-4">
                      <div className="text-xs">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="px-1.5 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-800/50 rounded font-mono text-[10px]">
                            담당: {act.owner_role}
                          </span>
                          <span className="px-1.5 py-0.5 bg-amber-950 text-amber-300 border border-amber-800/50 rounded font-mono text-[10px]">
                            우선순위: {act.priority}
                          </span>
                        </div>
                        <p className="text-slate-100 font-medium">{act.action}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Human Review Action Controls */}
                <div className="pt-3 border-t border-slate-700/60 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2 flex-1 min-w-[280px]">
                    <select
                      value={reviewerRole}
                      onChange={(e: any) => setReviewerRole(e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                      disabled={actionLoading}
                    >
                      <option value="CEO">대표이사 (CEO)</option>
                      <option value="GENERAL_MANAGER">총괄점장 (GM)</option>
                    </select>
                    <input
                      type="text"
                      placeholder="결재 의견 / 지시 사항 입력 (선택)"
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                      disabled={actionLoading}
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleReject(reviewerRole, commentText)}
                      disabled={actionLoading || isRejected}
                      className="px-3.5 py-1.5 bg-rose-900/60 hover:bg-rose-800/80 text-rose-200 text-xs font-semibold rounded-lg border border-rose-700/60 transition flex items-center gap-1.5 disabled:opacity-50"
                    >
                      <XCircle className="w-3.5 h-3.5" /> 반려 (Reject)
                    </button>
                    <button
                      onClick={() => handleApprove(reviewerRole, commentText)}
                      disabled={actionLoading || isApproved}
                      className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1.5 disabled:opacity-50"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" /> 승인 (Approve)
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Audit Trail Modal */}
      {showAuditModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl text-white">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <History className="w-4 h-4 text-indigo-400" /> 의사결정 감사 로그 (Audit Trail)
              </h3>
              <button
                onClick={() => setShowAuditModal(false)}
                className="text-slate-400 hover:text-white text-xs"
              >
                닫기
              </button>
            </div>
            <div className="max-h-72 overflow-y-auto space-y-3">
              {auditLogs.map((log) => (
                <div key={log.log_id} className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/50 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-indigo-300">{log.actor_role} ({log.action_type})</span>
                    <span className="text-[10px] text-slate-400 font-mono">{log.timestamp.slice(0, 19)}</span>
                  </div>
                  <p className="text-slate-300">
                    상태 변경: <span className="font-mono text-amber-300">{log.previous_status}</span> ➔ <span className="font-mono text-emerald-300">{log.new_status}</span>
                  </p>
                  {log.comment && (
                    <p className="text-slate-400 mt-1 bg-slate-900/60 p-1.5 rounded text-[11px]">
                      의견: {log.comment}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
""")


