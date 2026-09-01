import React from 'react';
import { DashboardSummaryResponse } from '../../types/dashboard';
import { formatWonSummary, formatPercent } from '../../utils/formatters';

interface SummarySectionProps {
  summary: DashboardSummaryResponse;
}

export const SummarySection: React.FC<SummarySectionProps> = ({ summary }) => {
  const isFoodCostIncomplete = summary.coverage.food_cost_ratio.available_days < summary.coverage.food_cost_ratio.total_days;

  return (
    <div
      data-testid="summary-section"
      style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23314e',
        borderRadius: '10px',
        padding: '18px 20px',
        marginTop: '24px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: 'bold', color: '#f8fafc', margin: '0 0 4px 0' }}>
            전체 기간 경영 요약 ({summary.start_date} ~ {summary.end_date})
          </h3>
          <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
            총 <strong>{summary.total_days}일</strong> 중 정상 집계 <strong>{summary.data_complete_days}일</strong> (결측 {summary.data_incomplete_days}일)
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', backgroundColor: '#450a0a', color: '#fca5a5' }}>
            CRITICAL {summary.critical_alert_count}건
          </span>
          <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', backgroundColor: '#431407', color: '#fdba74' }}>
            HIGH {summary.high_alert_count}건
          </span>
          <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', backgroundColor: '#422006', color: '#fef08a' }}>
            MEDIUM {summary.medium_alert_count}건
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        <div style={{ backgroundColor: '#0f172a', padding: '12px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8' }}>기간 총매출 / 일평균</div>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#38bdf8', marginTop: '2px' }}>
            {formatWonSummary(summary.total_sales)}
          </div>
          <div style={{ fontSize: '11px', color: '#64748b' }}>
            일평균 {formatWonSummary(summary.average_daily_sales)} (커버리지 100%)
          </div>
        </div>

        <div style={{ backgroundColor: '#0f172a', padding: '12px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8' }}>평균 인건비율</div>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#f8fafc', marginTop: '2px' }}>
            {formatPercent(summary.average_labor_ratio)}
          </div>
          <div style={{ fontSize: '11px', color: '#64748b' }}>
            {summary.coverage.labor_ratio.available_days} / {summary.coverage.labor_ratio.total_days}일 집계
          </div>
        </div>

        <div style={{ backgroundColor: '#0f172a', padding: '12px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
            <span>평균 원가율</span>
            {isFoodCostIncomplete && <span data-testid="coverage-warning" style={{ color: '#f59e0b', fontWeight: 'bold' }}>일부 누락</span>}
          </div>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#f8fafc', marginTop: '2px' }}>
            {formatPercent(summary.average_food_cost_ratio)}
          </div>
          <div style={{ fontSize: '11px', color: isFoodCostIncomplete ? '#f59e0b' : '#64748b' }}>
            {summary.coverage.food_cost_ratio.available_days} / {summary.coverage.food_cost_ratio.total_days}일 집계
          </div>
        </div>

        <div style={{ backgroundColor: '#0f172a', padding: '12px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8' }}>총 영업이익 / 평균 영업이익률</div>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#10b981', marginTop: '2px' }}>
            {formatWonSummary(summary.total_contribution)}
          </div>
          <div style={{ fontSize: '11px', color: '#64748b' }}>
            평균 {formatPercent(summary.average_contribution_ratio)}
          </div>
        </div>
      </div>
    </div>
  );
};
