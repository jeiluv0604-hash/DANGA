import { useState, useEffect, useCallback } from 'react';
import { DailyFactItem } from '../types/facts';
import { fetchDailyFacts } from '../api/facts';

function get7DaysBefore(dateStr: string): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() - 6);
  return d.toISOString().slice(0, 10);
}

export function useRecentTrends(targetDate: string) {
  const [facts, setFacts] = useState<DailyFactItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadTrends = useCallback(async () => {
    if (!targetDate) return;
    setLoading(true);
    setError(null);
    try {
      const startDate = get7DaysBefore(targetDate);
      const res = await fetchDailyFacts(startDate, targetDate);
      setFacts(res);
    } catch (err: any) {
      setError(err.message || '추세 데이터를 불러오지 못했습니다.');
      setFacts([]);
    } finally {
      setLoading(false);
    }
  }, [targetDate]);

  useEffect(() => {
    loadTrends();
  }, [loadTrends]);

  return { facts, loading, error, refetch: loadTrends };
}
