import { useState, useEffect, useCallback } from 'react';
import { DailyDashboardResponse } from '../types/dashboard';
import { fetchDailyDashboard } from '../api/dashboard';

export function useDailyDashboard(date: string) {
  const [data, setData] = useState<DailyDashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!date) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDailyDashboard(date);
      setData(res);
    } catch (err: any) {
      setError(err.message || '데이터를 불러오지 못했습니다.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [date]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return { data, loading, error, refetch: loadData };
}
