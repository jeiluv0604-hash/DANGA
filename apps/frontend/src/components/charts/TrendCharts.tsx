import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { DailyFactItem } from '../../types/facts';

interface TrendChartsProps {
  facts: DailyFactItem[];
}

export const TrendCharts: React.FC<TrendChartsProps> = ({ facts }) => {
  const chartData = facts.map((f) => ({
    date: f.business_date ? f.business_date.slice(5) : '',
    fullDate: f.business_date,
    salesMan: f.sales !== null ? Math.round(f.sales / 10000) : null,
    contributionMan: f.contribution !== null ? Math.round(f.contribution / 10000) : null,
    laborPct: f.labor_ratio !== null ? Number((f.labor_ratio * 100).toFixed(1)) : null,
    foodCostPct: f.food_cost_ratio !== null ? Number((f.food_cost_ratio * 100).toFixed(1)) : null,
  }));

  return (
    <div
      data-testid="trend-charts"
      style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23314e',
        borderRadius: '10px',
        padding: '18px 20px',
        marginBottom: '24px',
      }}
    >
      <div style={{ marginBottom: '16px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 'bold', color: '#f8fafc', margin: '0 0 4px 0' }}>
          최근 7일 경영 추세 (7-Day Trends)
        </h3>
        <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
          매출·수익성 및 원가 구조의 일별 변동 흐름 (결측 일자는 선 단절 처리)
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '20px',
        }}
      >
        <div style={{ height: '220px' }}>
          <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '8px' }}>
            매출 및 공헌이익 (단위: 만원)
          </div>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 15, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px', fontSize: '12px' }}
                formatter={(value: any) => [`${value}만원`, '']}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Line type="monotone" dataKey="salesMan" name="매출" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} connectNulls={false} />
              <Line type="monotone" dataKey="contributionMan" name="공헌이익" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={{ height: '220px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#94a3b8' }}>
              비용 비율 추이 (단위: %)
            </span>
            <span style={{ fontSize: '10px', color: '#f59e0b' }}>
              * 기준: 인건비 33% / 원가 38%
            </span>
          </div>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 15, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} domain={[15, 45]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px', fontSize: '12px' }}
                formatter={(value: any) => [`${value}%`, '']}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Line type="monotone" dataKey="laborPct" name="인건비율" stroke="#fb923c" strokeWidth={2} dot={{ r: 3 }} connectNulls={false} />
              <Line type="monotone" dataKey="foodCostPct" name="원가율" stroke="#f43f5e" strokeWidth={2} dot={{ r: 3 }} connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
