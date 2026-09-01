# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print('Wrote:', path)

# 1. KPI Cards & Grid
write_file('apps/frontend/src/components/kpi/KpiHeroCard.tsx', """import React from 'react';

interface KpiHeroCardProps {
  title: string;
  primaryValue: string;
  secondaryText?: string;
  subValue?: string;
  isWarning?: boolean;
  warningLabel?: string;
  isBlocked?: boolean;
}

export const KpiHeroCard: React.FC<KpiHeroCardProps> = ({
  title,
  primaryValue,
  secondaryText,
  subValue,
  isWarning = false,
  warningLabel,
  isBlocked = false,
}) => {
  return (
    <div
      data-testid="kpi-card"
      style={{
        backgroundColor: isBlocked ? '#161d2d' : isWarning ? '#231518' : '#131b2e',
        border: `1px solid ${isWarning ? '#dc2626' : isBlocked ? '#334155' : '#23314e'}`,
        borderRadius: '10px',
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
      }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>{title}</span>
          {isWarning && (
            <span
              style={{
                backgroundColor: '#450a0a',
                border: '1px solid #dc2626',
                color: '#f87171',
                fontSize: '11px',
                fontWeight: 'bold',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              {warningLabel || '경고'}
            </span>
          )}
          {isBlocked && (
            <span
              style={{
                backgroundColor: '#1e293b',
                color: '#94a3b8',
                fontSize: '11px',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              선행필드 누락
            </span>
          )}
        </div>

        <div
          data-testid="kpi-primary-value"
          style={{
            fontSize: '24px',
            fontWeight: '800',
            color: isBlocked ? '#94a3b8' : isWarning ? '#fca5a5' : '#f8fafc',
            letterSpacing: '-0.02em',
            marginBottom: '6px',
          }}
        >
          {primaryValue}
        </div>
      </div>

      <div>
        {subValue && (
          <div style={{ fontSize: '13px', fontWeight: '600', color: '#cbd5e1', marginBottom: '2px' }}>
            {subValue}
          </div>
        )}
        {secondaryText && (
          <div style={{ fontSize: '12px', color: '#64748b' }}>
            {secondaryText}
          </div>
        )}
      </div>
    </div>
  );
};
""")

write_file('apps/frontend/src/components/kpi/KpiGrid.tsx', """import React from 'react';
import { DailyKpis, KpiStatusMap, DailyAlert } from '../../types/dashboard';
import { KpiHeroCard } from './KpiHeroCard';
import { formatWon, formatPercent } from '../../utils/formatters';

interface KpiGridProps {
  kpis: DailyKpis;
  kpiStatus: KpiStatusMap;
  alerts: DailyAlert[];
}

export const KpiGrid: React.FC<KpiGridProps> = ({ kpis, kpiStatus, alerts }) => {
  const hasLaborAlert = alerts.some((a) => a.rule_id === 'R-LAB-01');
  const hasFoodCostAlert = alerts.some((a) => a.rule_id === 'R-FC-01');

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '16px',
        marginBottom: '24px',
      }}
    >
      <KpiHeroCard
        title="오늘 매출 (Sales)"
        primaryValue={formatWon(kpis.sales, kpiStatus.sales)}
        subValue={`고객 ${kpis.guests ? `${kpis.guests}명` : '데이터 없음'}`}
        secondaryText={`객단가 ${formatWon(kpis.avg_check, kpiStatus.avg_check)}`}
      />

      <KpiHeroCard
        title="인건비율 (Labor Ratio)"
        primaryValue={formatPercent(kpis.labor_ratio, kpiStatus.labor_ratio)}
        subValue={`인건비 ${formatWon(kpis.labor_cost, kpiStatus.labor_cost)}`}
        secondaryText="적정 기준 33.0% 이하"
        isWarning={hasLaborAlert}
        warningLabel="인건비 초과"
      />

      <KpiHeroCard
        title="식재료 원가율 (Food Cost Ratio)"
        primaryValue={formatPercent(kpis.food_cost_ratio, kpiStatus.food_cost_ratio)}
        subValue={`식재료비 ${formatWon(kpis.food_cost, kpiStatus.food_cost)}`}
        secondaryText="적정 기준 38.0% 이하"
        isWarning={hasFoodCostAlert}
        warningLabel="원가율 초과"
        isBlocked={kpiStatus.food_cost_ratio === 'BLOCKED_DEPENDENCY'}
      />

      <KpiHeroCard
        title="공헌이익 (Contribution)"
        primaryValue={formatWon(kpis.contribution, kpiStatus.contribution)}
        subValue={`공헌이익률 ${formatPercent(kpis.contribution_ratio, kpiStatus.contribution_ratio)}`}
        secondaryText="매출 - (인건비 + 식재료비)"
        isBlocked={kpiStatus.contribution === 'BLOCKED_DEPENDENCY'}
      />
    </div>
  );
};
""")

# 2. Alerts
write_file('apps/frontend/src/components/alerts/AlertCard.tsx', """import React from 'react';
import { DailyAlert } from '../../types/dashboard';
import { getRuleMeta } from '../../utils/ruleDisplay';
import { getSeverityStyle } from '../../utils/status';

interface AlertCardProps {
  alert: DailyAlert;
  onOpenEvidence: (evidenceId: string) => void;
}

export const AlertCard: React.FC<AlertCardProps> = ({ alert, onOpenEvidence }) => {
  const meta = getRuleMeta(alert.rule_id);
  const style = getSeverityStyle(alert.severity);

  return (
    <div
      data-testid="alert-card"
      style={{
        backgroundColor: style.badgeBg,
        border: `1px solid ${style.border}`,
        borderRadius: '8px',
        padding: '14px 16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '10px',
      }}
    >
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span
            style={{
              backgroundColor: style.indicator,
              color: '#000',
              fontSize: '10px',
              fontWeight: '900',
              padding: '2px 6px',
              borderRadius: '4px',
            }}
          >
            {style.label}
          </span>
          <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#f8fafc' }}>
            {meta.name}
          </span>
          <span style={{ fontSize: '11px', color: '#64748b', fontFamily: 'monospace' }}>
            {alert.rule_id}
          </span>
        </div>

        <p style={{ fontSize: '12px', color: '#cbd5e1', margin: '0 0 4px 0' }}>
          {meta.description}
        </p>

        <div style={{ fontSize: '12px', color: style.badgeText, display: 'flex', gap: '12px' }}>
          <span><strong>관측치:</strong> {alert.actual_value}</span>
          <span><strong>관리기준:</strong> {alert.threshold_value}</span>
        </div>
      </div>

      {alert.evidence_id && (
        <button
          onClick={() => onOpenEvidence(alert.evidence_id!)}
          aria-label="Evidence 확인"
          style={{
            padding: '6px 12px',
            backgroundColor: '#1e293b',
            border: '1px solid #3b82f6',
            color: '#38bdf8',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            whiteSpace: 'nowrap',
          }}
        >
          Evidence 확인
        </button>
      )}
    </div>
  );
};
""")

write_file('apps/frontend/src/components/alerts/AlertPriorityPanel.tsx', """import React from 'react';
import { DailyAlert } from '../../types/dashboard';
import { AlertCard } from './AlertCard';
import { EmptyState } from '../common/EmptyState';

interface AlertPriorityPanelProps {
  alerts: DailyAlert[];
  onOpenEvidence: (evidenceId: string) => void;
}

export const AlertPriorityPanel: React.FC<AlertPriorityPanelProps> = ({ alerts, onOpenEvidence }) => {
  const severityWeight = {
    CRITICAL: 3,
    HIGH: 2,
    MEDIUM: 1,
  };

  const sortedAlerts = [...alerts].sort(
    (a, b) => (severityWeight[b.severity] || 0) - (severityWeight[a.severity] || 0)
  );

  return (
    <div
      data-testid="alert-priority-panel"
      style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23314e',
        borderRadius: '10px',
        padding: '18px 20px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 'bold', color: '#f8fafc', margin: 0 }}>
          오늘의 경영 이상 경보 (Alert Priority)
        </h3>
        <span style={{ fontSize: '12px', color: '#94a3b8' }}>
          총 <strong>{alerts.length}</strong>건
        </span>
      </div>

      {sortedAlerts.length === 0 ? (
        <EmptyState message="오늘 등록된 이상 경보가 없습니다. 모든 경영 지표가 정상 범위입니다." />
      ) : (
        <div>
          {sortedAlerts.map((alert) => (
            <AlertCard key={alert.alert_id} alert={alert} onOpenEvidence={onOpenEvidence} />
          ))}
        </div>
      )}
    </div>
  );
};
""")

# 3. Panels: Inventory & Customer
write_file('apps/frontend/src/components/panels/InventoryPanel.tsx', """import React from 'react';
import { DailyKpis, KpiStatusMap, DailyAlert } from '../../types/dashboard';
import { formatKg, formatPercent } from '../../utils/formatters';

interface InventoryPanelProps {
  kpis: DailyKpis;
  kpiStatus: KpiStatusMap;
  alerts: DailyAlert[];
}

export const InventoryPanel: React.FC<InventoryPanelProps> = ({ kpis, kpiStatus, alerts }) => {
  const hasInvAlert = alerts.some((a) => a.rule_id === 'R-INV-01');
  const hasWasteAlert = alerts.some((a) => a.rule_id === 'R-WST-01');

  return (
    <div
      data-testid="inventory-panel"
      style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23314e',
        borderRadius: '10px',
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 'bold', color: '#f8fafc', margin: 0 }}>
            식재료 재고 & 폐기 상태
          </h3>
          {(hasInvAlert || hasWasteAlert) && (
            <span
              style={{
                backgroundColor: '#450a0a',
                color: '#f87171',
                fontSize: '11px',
                fontWeight: 'bold',
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid #dc2626',
              }}
            >
              확인 필요
            </span>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '12px' }}>
          <div style={{ backgroundColor: '#0f172a', padding: '10px', borderRadius: '6px' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>재고 차이</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: (kpis.inventory_variance_kg || 0) < -2.0 ? '#f87171' : '#f8fafc' }}>
              {formatKg(kpis.inventory_variance_kg, kpiStatus.inventory_variance)}
            </div>
          </div>

          <div style={{ backgroundColor: '#0f172a', padding: '10px', borderRadius: '6px' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>폐기율</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: (kpis.waste_ratio || 0) >= 0.02 ? '#fb923c' : '#f8fafc' }}>
              {formatPercent(kpis.waste_ratio, kpiStatus.waste_ratio)}
            </div>
          </div>

          <div style={{ backgroundColor: '#0f172a', padding: '10px', borderRadius: '6px' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>서비스 제공</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#f8fafc' }}>
              {formatKg(kpis.service_kg, kpiStatus.service_kg)}
            </div>
          </div>
        </div>
      </div>

      <p style={{ fontSize: '11px', color: '#64748b', margin: 0, lineHeight: 1.4 }}>
        * 재고 차이는 실사 수기 기록과 전산 출고 간의 확인 대상 지표이며, 이상 감지 시 현장 실사를 권고합니다.
      </p>
    </div>
  );
};
""")

write_file('apps/frontend/src/components/panels/CustomerPanel.tsx', """import React from 'react';
import { DailyKpis, KpiStatusMap, DailyAlert } from '../../types/dashboard';
import { formatRating, formatCount } from '../../utils/formatters';

interface CustomerPanelProps {
  kpis: DailyKpis;
  kpiStatus: KpiStatusMap;
  alerts: DailyAlert[];
}

export const CustomerPanel: React.FC<CustomerPanelProps> = ({ kpis, kpiStatus, alerts }) => {
  const hasCustAlert = alerts.some((a) => a.rule_id === 'R-CUS-01');

  return (
    <div
      data-testid="customer-panel"
      style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23314e',
        borderRadius: '10px',
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 'bold', color: '#f8fafc', margin: 0 }}>
            고객 반응 & 서비스 품질
          </h3>
          {hasCustAlert && (
            <span
              style={{
                backgroundColor: '#422006',
                color: '#fde047',
                fontSize: '11px',
                fontWeight: 'bold',
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid #eab308',
              }}
            >
              주의 필요
            </span>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '12px' }}>
          <div style={{ backgroundColor: '#0f172a', padding: '10px', borderRadius: '6px' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>고객 평점</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: (kpis.rating || 5) <= 4.2 ? '#f87171' : '#f8fafc' }}>
              {formatRating(kpis.rating, kpiStatus.rating)}
              {kpis.rating !== null && <span style={{ fontSize: '11px', color: '#94a3b8' }}> / 5.0</span>}
            </div>
          </div>

          <div style={{ backgroundColor: '#0f172a', padding: '10px', borderRadius: '6px' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>불만 접수</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: (kpis.complaints || 0) >= 3 ? '#f87171' : '#f8fafc' }}>
              {formatCount(kpis.complaints, '건', kpiStatus.complaints)}
            </div>
          </div>

          <div style={{ backgroundColor: '#0f172a', padding: '10px', borderRadius: '6px' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>리뷰 등록</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#f8fafc' }}>
              {formatCount(kpis.review_count, '건', kpiStatus.review_count)}
            </div>
          </div>
        </div>
      </div>

      <p style={{ fontSize: '11px', color: '#64748b', margin: 0, lineHeight: 1.4 }}>
        * 일일 네이버/카카오 리뷰 및 현장 매니저 접수 불만을 종합 집계한 수치입니다.
      </p>
    </div>
  );
};
""")

# 4. Trend Charts
write_file('apps/frontend/src/components/charts/TrendCharts.tsx', """import React from 'react';
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
""")

# 5. Summary Section
write_file('apps/frontend/src/components/summary/SummarySection.tsx', """import React from 'react';
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
          <div style={{ fontSize: '11px', color: '#94a3b8' }}>총 공헌이익 / 평균 이익률</div>
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
""")

# 6. Evidence Drawer
write_file('apps/frontend/src/components/evidence/EvidenceDrawer.tsx', """import React, { useEffect, useState } from 'react';
import { EvidenceDetail, EvidenceVerifyResult } from '../../types/evidence';
import { fetchEvidenceDetail, verifyEvidence } from '../../api/evidence';
import { truncateHash } from '../../utils/formatters';

interface EvidenceDrawerProps {
  evidenceId: string | null;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({ evidenceId, onClose }) => {
  const [detail, setDetail] = useState<EvidenceDetail | null>(null);
  const [verify, setVerify] = useState<EvidenceVerifyResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!evidenceId) return;
    setLoading(true);
    setError(null);
    Promise.all([fetchEvidenceDetail(evidenceId), verifyEvidence(evidenceId)])
      .then(([d, v]) => {
        setDetail(d);
        setVerify(v);
      })
      .catch((err: any) => {
        setError(err.message || '증적 정보를 불러오지 못했습니다.');
      })
      .finally(() => setLoading(false));
  }, [evidenceId]);

  if (!evidenceId) return null;

  return (
    <div
      data-testid="evidence-drawer"
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '100%',
        maxWidth: '460px',
        backgroundColor: '#0f172a',
        borderLeft: '1px solid #334155',
        boxShadow: '-4px 0 20px rgba(0,0,0,0.6)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid #1e293b',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold', color: '#f8fafc', margin: 0 }}>
            증적(Evidence) 무결성 검증
          </h3>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>ID: {evidenceId}</span>
        </div>
        <button
          onClick={onClose}
          aria-label="닫기"
          style={{
            padding: '4px 8px',
            backgroundColor: '#1e293b',
            color: '#cbd5e1',
            borderRadius: '4px',
            fontSize: '14px',
            fontWeight: 'bold',
          }}
        >
          ✕
        </button>
      </div>

      <div style={{ padding: '20px', overflowY: 'auto', flex: 1 }}>
        {loading ? (
          <div style={{ color: '#94a3b8', textAlign: 'center', padding: '40px 0' }}>
            증적 파일 암호화 검증 중...
          </div>
        ) : error ? (
          <div style={{ color: '#f87171', padding: '20px', backgroundColor: '#450a0a', borderRadius: '6px' }}>
            {error}
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>암호화 해시 검증 상태</div>
              {verify?.integrity === 'VALID' ? (
                <div
                  data-testid="evidence-status-valid"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    backgroundColor: '#064e3b',
                    border: '1px solid #10b981',
                    color: '#a7f3d0',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    fontSize: '14px',
                  }}
                >
                  <span>✓</span>
                  <span>무결성 검증됨 (VALID)</span>
                </div>
              ) : verify?.integrity === 'INVALID' ? (
                <div
                  data-testid="evidence-status-invalid"
                  style={{
                    backgroundColor: '#450a0a',
                    border: '1px solid #ef4444',
                    color: '#fecaca',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    fontSize: '14px',
                  }}
                >
                  <span>⚠</span>
                  <span>무결성 검증 실패 (INVALID - 파일 위변조 감지)</span>
                </div>
              ) : (
                <div
                  style={{
                    backgroundColor: '#431407',
                    border: '1px solid #f97316',
                    color: '#fed7aa',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    fontSize: '14px',
                  }}
                >
                  <span>?</span>
                  <span>증적 파일 없음 (MISSING_FILE)</span>
                </div>
              )}
            </div>

            <div style={{ backgroundColor: '#131b2e', borderRadius: '8px', padding: '14px', marginBottom: '20px' }}>
              <h4 style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '10px' }}>증적 메타데이터</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>발생 일자</span>
                  <span style={{ color: '#f8fafc', fontWeight: 'bold' }}>{detail?.business_date || '-'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>규칙 ID</span>
                  <span style={{ color: '#f8fafc', fontFamily: 'monospace' }}>{detail?.rule_id || '-'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>파일 경로</span>
                  <span style={{ color: '#94a3b8', fontFamily: 'monospace' }}>{detail?.file_path || '-'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Evidence SHA-256</span>
                  <span style={{ color: '#38bdf8', fontFamily: 'monospace' }} title={detail?.file_sha256}>
                    {truncateHash(detail?.file_sha256)}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Dataset SHA-256</span>
                  <span style={{ color: '#94a3b8', fontFamily: 'monospace' }} title={detail?.dataset_sha256}>
                    {truncateHash(detail?.dataset_sha256)}
                  </span>
                </div>
              </div>
            </div>

            <p style={{ fontSize: '11px', color: '#64748b', lineHeight: 1.4 }}>
              * 본 증적 검증은 디스크에 저장된 증적 파일 바이트로부터 SHA-256을 실시간 계산하여 원본 등록 해시와 100% 일치함을 보증합니다.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
""")

# 7. CeoCockpitPage & Entrypoints
write_file('apps/frontend/src/pages/CeoCockpitPage.tsx', """import React, { useState } from 'react';
import { Header } from '../components/layout/Header';
import { DataIncompleteBanner } from '../components/layout/DataIncompleteBanner';
import { KpiGrid } from '../components/kpi/KpiGrid';
import { AlertPriorityPanel } from '../components/alerts/AlertPriorityPanel';
import { TrendCharts } from '../components/charts/TrendCharts';
import { InventoryPanel } from '../components/panels/InventoryPanel';
import { CustomerPanel } from '../components/panels/CustomerPanel';
import { SummarySection } from '../components/summary/SummarySection';
import { EvidenceDrawer } from '../components/evidence/EvidenceDrawer';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorState } from '../components/common/ErrorState';
import { useDailyDashboard } from '../hooks/useDailyDashboard';
import { useRecentTrends } from '../hooks/useRecentTrends';
import { useSummary } from '../hooks/useSummary';

export const CeoCockpitPage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>('2026-08-31');
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null);

  const { data: dailyData, loading: dailyLoading, error: dailyError, refetch: refetchDaily } = useDailyDashboard(selectedDate);
  const { facts: trendFacts } = useRecentTrends(selectedDate);
  const { summary: summaryData } = useSummary();

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#090d16', color: '#f8fafc' }}>
      <Header currentDate={selectedDate} onDateChange={setSelectedDate} />

      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
        {dailyLoading ? (
          <LoadingSkeleton />
        ) : dailyError ? (
          <ErrorState message={dailyError} onRetry={refetchDaily} />
        ) : dailyData ? (
          <div>
            {dailyData.data_status === 'DATA_INCOMPLETE' && (
              <DataIncompleteBanner date={dailyData.date} />
            )}

            <KpiGrid
              kpis={dailyData.kpis}
              kpiStatus={dailyData.kpi_status}
              alerts={dailyData.alerts}
            />

            <TrendCharts facts={trendFacts} />

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '16px',
                marginBottom: '24px',
              }}
            >
              <AlertPriorityPanel
                alerts={dailyData.alerts}
                onOpenEvidence={(id) => setActiveEvidenceId(id)}
              />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <InventoryPanel
                  kpis={dailyData.kpis}
                  kpiStatus={dailyData.kpi_status}
                  alerts={dailyData.alerts}
                />
                <CustomerPanel
                  kpis={dailyData.kpis}
                  kpiStatus={dailyData.kpi_status}
                  alerts={dailyData.alerts}
                />
              </div>
            </div>

            {summaryData && <SummarySection summary={summaryData} />}
          </div>
        ) : null}
      </main>

      <EvidenceDrawer
        evidenceId={activeEvidenceId}
        onClose={() => setActiveEvidenceId(null)}
      />
    </div>
  );
};
""")

write_file('apps/frontend/src/App.tsx', """import React from 'react';
import { CeoCockpitPage } from './pages/CeoCockpitPage';

export const App: React.FC = () => {
  return <CeoCockpitPage />;
};

export default App;
""")

write_file('apps/frontend/src/main.tsx', """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
""")


