import React, { useEffect, useMemo, useState } from 'react';
import { CalendarRange, CircleDollarSign, TrendingUp } from 'lucide-react';

import { getManagementPrototype } from '../../api/management';
import { ManagementPrototype } from '../../types/management';

type ManagementView = 'monthly' | 'yearly';

interface ManagementSystemSectionProps {
  view: ManagementView;
}

const won = (value: number) => `${new Intl.NumberFormat('ko-KR').format(value)}원`;
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
const metricLabels: Record<string, string> = { sales: '매출', food_cost: '식재료비', labor_cost: '인건비', operating_profit: '영업이익' };

const panelStyle: React.CSSProperties = {
  background: '#131b2e',
  border: '1px solid #23314e',
  borderRadius: '12px',
  padding: '18px',
};

const metricStyle: React.CSSProperties = {
  ...panelStyle,
  minHeight: '112px',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
};

export const ManagementSystemSection: React.FC<ManagementSystemSectionProps> = ({ view }) => {
  const [data, setData] = useState<ManagementPrototype | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    getManagementPrototype()
      .then((response) => mounted && setData(response))
      .catch((reason: Error) => mounted && setError(reason.message));
    return () => { mounted = false; };
  }, []);

  const yearly = useMemo(() => {
    if (!data) return null;
    const months = data.finance.monthly_pnl;
    const sum = (key: 'sales' | 'food_cost' | 'labor_cost' | 'operating_profit') =>
      months.reduce((total, item) => total + item[key], 0);
    const recordedSales = sum('sales');
    const recordedProfit = sum('operating_profit');
    return {
      year: months[0]?.period.slice(0, 4) ?? '2026',
      months: months.length,
      recordedSales,
      recordedProfit,
      projectedSales: data.finance.annualized_sales_baseline ?? (months.length ? Math.round(recordedSales * 12 / months.length) : 0),
      projectedProfit: months.length ? Math.round(recordedProfit * 12 / months.length) : 0,
      foodCost: sum('food_cost'),
      laborCost: sum('labor_cost'),
    };
  }, [data]);

  if (error) return <section style={{ ...panelStyle, color: '#fca5a5' }}>매출 정보를 불러오지 못했습니다: {error}</section>;
  if (!data || !yearly) return <section style={panelStyle}>담가화로구이 매출 정보를 불러오는 중입니다.</section>;

  if (view === 'yearly') {
    const recordedMargin = yearly.recordedSales ? yearly.recordedProfit / yearly.recordedSales : 0;
    return (
      <section data-testid="yearly-sales-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
          <CalendarRange size={20} color="#38bdf8" />
          <div><h2 style={{ fontSize: '17px' }}>{yearly.year}년 매출 정보</h2><p style={{ color: '#94a3b8', fontSize: '12px' }}>{yearly.months}개월 가상 실적과 연환산 전망</p></div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '12px', marginBottom: '16px' }}>
          <div style={metricStyle}><span style={{ color: '#94a3b8', fontSize: '12px' }}>누적 매출</span><strong style={{ fontSize: '23px', marginTop: '6px', color: '#38bdf8' }}>{won(yearly.recordedSales)}</strong></div>
          <div style={metricStyle}><span style={{ color: '#94a3b8', fontSize: '12px' }}>연환산 예상 매출</span><strong style={{ fontSize: '23px', marginTop: '6px' }}>{won(yearly.projectedSales)}</strong></div>
          <div style={metricStyle}><span style={{ color: '#94a3b8', fontSize: '12px' }}>누적 영업이익</span><strong style={{ fontSize: '23px', marginTop: '6px', color: '#6ee7b7' }}>{won(yearly.recordedProfit)}</strong><small style={{ color: '#94a3b8' }}>영업이익률 {percent(recordedMargin)}</small></div>
          <div style={metricStyle}><span style={{ color: '#94a3b8', fontSize: '12px' }}>연환산 예상 영업이익</span><strong style={{ fontSize: '23px', marginTop: '6px' }}>{won(yearly.projectedProfit)}</strong></div>
        </div>
        <div style={panelStyle}>
          <h3 style={{ fontSize: '14px', marginBottom: '12px' }}>연간 비용 구조 확인</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
            <div><span style={{ color: '#94a3b8', fontSize: '12px' }}>누적 식재료비</span><div style={{ fontWeight: 700 }}>{won(yearly.foodCost)}</div></div>
            <div><span style={{ color: '#94a3b8', fontSize: '12px' }}>누적 인건비</span><div style={{ fontWeight: 700 }}>{won(yearly.laborCost)}</div></div>
            <div><span style={{ color: '#94a3b8', fontSize: '12px' }}>데이터 기준</span><div style={{ fontWeight: 700, color: '#fbbf24' }}>{data.dataset_type}</div></div>
            <div><span style={{ color: '#94a3b8', fontSize: '12px' }}>비용 배부 기준</span><div style={{ fontWeight: 700, color: '#c4b5fd' }}>{data.finance.allocation_policy_status}</div></div>
          </div>
        </div>
      </section>
    );
  }

  const latest = data.finance.monthly_pnl[data.finance.monthly_pnl.length - 1];
  const latestCash = data.finance.cash_flow[data.finance.cash_flow.length - 1];
  const latestBudget = data.finance.budget_actual[data.finance.budget_actual.length - 1];

  return (
    <section data-testid="monthly-sales-panel">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
        <CircleDollarSign size={20} color="#10b981" />
        <div><h2 style={{ fontSize: '17px' }}>월 단위 매출 정보</h2><p style={{ color: '#94a3b8', fontSize: '12px' }}>월별 매출·비용·영업이익과 현금흐름</p></div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        {([['월 매출', won(latest.sales), '#38bdf8'], ['영업이익', won(latest.operating_profit), '#6ee7b7'], ['영업이익률', percent(latest.operating_margin), '#f8fafc'], ['기말 현금', won(latestCash.ending_cash), '#f8fafc']] as Array<[string, string, string]>).map(([label, value, color]) => (
          <div key={label} style={metricStyle}><span style={{ color: '#94a3b8', fontSize: '12px' }}>{latest.period} · {label}</span><strong style={{ fontSize: '22px', marginTop: '6px', color }}>{value}</strong></div>
        ))}
      </div>
      <div style={{ ...panelStyle, marginBottom: '16px', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', minWidth: '680px' }}>
          <thead><tr style={{ color: '#94a3b8' }}><th style={{ textAlign: 'left', padding: '8px' }}>월</th><th>매출</th><th>식재료비</th><th>인건비</th><th>영업이익</th><th>영업이익률</th></tr></thead>
          <tbody>{data.finance.monthly_pnl.map((item) => <tr key={item.period} style={{ borderTop: '1px solid #23314e', textAlign: 'right' }}><td style={{ padding: '10px 8px', textAlign: 'left' }}>{item.period}</td><td>{won(item.sales)}</td><td>{won(item.food_cost)}</td><td>{won(item.labor_cost)}</td><td style={{ color: '#6ee7b7', fontWeight: 700 }}>{won(item.operating_profit)}</td><td>{percent(item.operating_margin)}</td></tr>)}</tbody>
        </table>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '12px' }}>
        <div style={panelStyle}>
          <h3 style={{ fontSize: '13px', marginBottom: '8px' }}><TrendingUp size={15} style={{ verticalAlign: 'middle', marginRight: '6px' }} />예산 대비 실적</h3>
          {Object.entries(latestBudget.metrics).slice(0, 4).map(([metric, values]) => <div key={metric} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', borderTop: '1px solid #23314e', padding: '7px 0', fontSize: '11px' }}><strong>{metricLabels[metric] ?? metric}</strong><span>실적 {won(values.actual)}</span><span style={{ color: values.variance >= 0 ? '#6ee7b7' : '#fca5a5' }}>차이 {won(values.variance)}</span></div>)}
        </div>
        <div style={panelStyle}><h3 style={{ fontSize: '13px', marginBottom: '8px' }}>현금흐름</h3><p style={{ color: '#cbd5e1', fontSize: '12px', lineHeight: 1.8 }}>기초 {won(latestCash.beginning_cash)}<br />+ 유입 {won(latestCash.cash_inflows)}<br />- 유출 {won(latestCash.cash_outflows)}<br /><strong style={{ color: '#6ee7b7' }}>= 기말 {won(latestCash.ending_cash)}</strong></p></div>
      </div>
      <p style={{ color: '#a78bfa', fontSize: '11px', marginTop: '12px' }}>비용 계정·부문별 배부 기준: {data.finance.allocation_policy_status}</p>
    </section>
  );
};
