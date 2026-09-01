import { useState, useEffect, useCallback } from 'react';
import { DashboardSummaryResponse } from '../types/dashboard';
import { fetchDashboardSummary } from '../api/dashboard';

export function useSummary(startDate?: string, endDate?: string) {
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDashboardSummary(startDate, endDate);
      setSummary(res);
    } catch (err: any) {
      setError(err.message || '요약 데이터를 불러오지 못했습니다.');
      setSummary(null);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  return { summary, loading, error, refetch: loadSummary };
}
