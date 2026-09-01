import { useState, useEffect, useCallback } from 'react';
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
