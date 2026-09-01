# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print('Wrote:', path)

# 1. Hooks
write_file('apps/frontend/src/hooks/useDailyDashboard.ts', """import { useState, useEffect, useCallback } from 'react';
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
""")

write_file('apps/frontend/src/hooks/useRecentTrends.ts', """import { useState, useEffect, useCallback } from 'react';
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
""")

write_file('apps/frontend/src/hooks/useSummary.ts', """import { useState, useEffect, useCallback } from 'react';
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
""")

# 2. Layout Components
write_file('apps/frontend/src/components/layout/SyntheticBadge.tsx', """import React from 'react';

export const SyntheticBadge: React.FC = () => {
  return (
    <div
      data-testid="synthetic-badge"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        backgroundColor: '#422006',
        border: '1px solid #d97706',
        color: '#fef3c7',
        padding: '4px 10px',
        borderRadius: '6px',
        fontSize: '12px',
        fontWeight: 'bold',
        letterSpacing: '0.02em',
        boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
      }}
    >
      <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
      <span>SYNTHETIC · 실제 매장 데이터 아님</span>
    </div>
  );
};
""")

write_file('apps/frontend/src/components/layout/DateSelector.tsx', """import React from 'react';

interface DateSelectorProps {
  currentDate: string;
  onDateChange: (date: string) => void;
  minDate?: string;
  maxDate?: string;
}

export const DateSelector: React.FC<DateSelectorProps> = ({
  currentDate,
  onDateChange,
  minDate = '2026-06-01',
  maxDate = '2026-08-31',
}) => {
  const handlePrev = () => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() - 1);
    const prevStr = d.toISOString().slice(0, 10);
    if (!minDate || prevStr >= minDate) {
      onDateChange(prevStr);
    }
  };

  const handleNext = () => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() + 1);
    const nextStr = d.toISOString().slice(0, 10);
    if (!maxDate || nextStr <= maxDate) {
      onDateChange(nextStr);
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <button
        onClick={handlePrev}
        disabled={minDate ? currentDate <= minDate : false}
        aria-label="이전 날짜"
        style={{
          padding: '6px 12px',
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '6px',
          color: '#f8fafc',
          fontSize: '13px',
          cursor: currentDate <= minDate ? 'not-allowed' : 'pointer',
          opacity: currentDate <= minDate ? 0.5 : 1,
        }}
      >
        ◀ 이전일
      </button>

      <input
        type="date"
        value={currentDate}
        min={minDate}
        max={maxDate}
        onChange={(e) => e.target.value && onDateChange(e.target.value)}
        aria-label="영업일 선택"
        style={{
          padding: '6px 10px',
          backgroundColor: '#0f172a',
          border: '1px solid #3b82f6',
          borderRadius: '6px',
          color: '#f8fafc',
          fontSize: '14px',
          fontWeight: '600',
          outline: 'none',
        }}
      />

      <button
        onClick={handleNext}
        disabled={maxDate ? currentDate >= maxDate : false}
        aria-label="다음 날짜"
        style={{
          padding: '6px 12px',
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '6px',
          color: '#f8fafc',
          fontSize: '13px',
          cursor: currentDate >= maxDate ? 'not-allowed' : 'pointer',
          opacity: currentDate >= maxDate ? 0.5 : 1,
        }}
      >
        다음일 ▶
      </button>
    </div>
  );
};
""")

write_file('apps/frontend/src/components/layout/Header.tsx', """import React from 'react';
import { SyntheticBadge } from './SyntheticBadge';
import { DateSelector } from './DateSelector';

interface HeaderProps {
  currentDate: string;
  onDateChange: (date: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ currentDate, onDateChange }) => {
  return (
    <header
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 24px',
        backgroundColor: '#0b1120',
        borderBottom: '1px solid #1e293b',
        gap: '16px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            backgroundColor: '#d97706',
            color: '#000',
            fontWeight: '900',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '14px',
          }}
        >
          DAMGA
        </div>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 'bold', color: '#f8fafc', margin: 0 }}>
            담가화로구이 CEO Cockpit
          </h1>
          <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
            단일 매장 통합 경영자동화 시스템 (연매출 42억 기준)
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <DateSelector currentDate={currentDate} onDateChange={onDateChange} />
        <SyntheticBadge />
      </div>
    </header>
  );
};
""")

write_file('apps/frontend/src/components/layout/DataIncompleteBanner.tsx', """import React from 'react';

interface DataIncompleteBannerProps {
  date: string;
}

export const DataIncompleteBanner: React.FC<DataIncompleteBannerProps> = ({ date }) => {
  return (
    <div
      data-testid="data-incomplete-banner"
      style={{
        backgroundColor: '#450a0a',
        border: '1px solid #dc2626',
        borderRadius: '8px',
        padding: '14px 18px',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
      }}
    >
      <span style={{ fontSize: '20px' }}>⚠️</span>
      <div>
        <h4 style={{ color: '#fecaca', fontSize: '15px', fontWeight: 'bold', margin: '0 0 4px 0' }}>
          일부 필수 데이터가 누락되었습니다 ({date})
        </h4>
        <p style={{ color: '#fca5a5', fontSize: '13px', margin: 0, lineHeight: 1.4 }}>
          Food Cost 데이터가 입력되지 않아 <strong>식재료 원가율</strong> 및 <strong>공헌이익</strong>을 계산할 수 없습니다 (계산 불가 표기).
          <br />
          매출·객수·인건비·재고·고객 평점 등 <strong>독립 관측치</strong>는 신뢰성 있게 정상 보존되어 표시됩니다.
        </p>
      </div>
    </div>
  );
};
""")

# 3. Common Components
write_file('apps/frontend/src/components/common/LoadingSkeleton.tsx', """import React from 'react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <div style={{ padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ height: '48px', backgroundColor: '#1e293b', borderRadius: '8px' }} className="animate-pulse-subtle" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} style={{ height: '140px', backgroundColor: '#131b2e', borderRadius: '10px', border: '1px solid #1e293b' }} className="animate-pulse-subtle" />
        ))}
      </div>
      <div style={{ height: '240px', backgroundColor: '#131b2e', borderRadius: '10px', border: '1px solid #1e293b' }} className="animate-pulse-subtle" />
    </div>
  );
};
""")

write_file('apps/frontend/src/components/common/ErrorState.tsx', """import React from 'react';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ message, onRetry }) => {
  return (
    <div
      style={{
        padding: '60px 24px',
        textAlign: 'center',
        backgroundColor: '#131b2e',
        borderRadius: '12px',
        margin: '24px',
        border: '1px solid #334155',
      }}
    >
      <div style={{ fontSize: '36px', marginBottom: '12px' }}>⚡</div>
      <h3 style={{ fontSize: '18px', color: '#f8fafc', marginBottom: '8px' }}>
        데이터를 불러오지 못했습니다
      </h3>
      <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '20px' }}>{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '8px 20px',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            borderRadius: '6px',
            fontWeight: '600',
            fontSize: '14px',
          }}
        >
          다시 시도
        </button>
      )}
    </div>
  );
};
""")

write_file('apps/frontend/src/components/common/EmptyState.tsx', """import React from 'react';

interface EmptyStateProps {
  message: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ message }) => {
  return (
    <div
      style={{
        padding: '40px 20px',
        textAlign: 'center',
        color: '#64748b',
        fontSize: '14px',
        backgroundColor: '#0f172a',
        borderRadius: '8px',
        border: '1px dashed #1e293b',
      }}
    >
      {message}
    </div>
  );
};
""")

