import React from 'react';
import { DailyKpis, KpiStatusMap, DailyAlert } from '../../types/dashboard';
import { KpiHeroCard } from './KpiHeroCard';
import { formatWon, formatPercent } from '../../utils/formatters';

interface KpiGridProps {
  kpis: DailyKpis;
  kpiStatus: KpiStatusMap;
  alerts: DailyAlert[];
  includeSales?: boolean;
}

export const KpiGrid: React.FC<KpiGridProps> = ({ kpis, kpiStatus, alerts, includeSales = true }) => {
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
      {includeSales && (
        <KpiHeroCard
          title="오늘 매출 (Sales)"
          primaryValue={formatWon(kpis.sales, kpiStatus.sales)}
          subValue={`고객 ${kpis.guests ? `${kpis.guests}명` : '데이터 없음'}`}
          secondaryText={`객단가 ${formatWon(kpis.avg_check, kpiStatus.avg_check)}`}
        />
      )}

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
        secondaryText="적정 기준 39.0% 이하"
        isWarning={hasFoodCostAlert}
        warningLabel="원가율 초과"
        isBlocked={kpiStatus.food_cost_ratio === 'BLOCKED_DEPENDENCY'}
      />

      <KpiHeroCard
        title="영업이익"
        primaryValue={formatWon(kpis.contribution, kpiStatus.contribution)}
        subValue={`영업이익률 ${formatPercent(kpis.contribution_ratio, kpiStatus.contribution_ratio)}`}
        secondaryText="매출 - (인건비 + 식재료비)"
        isBlocked={kpiStatus.contribution === 'BLOCKED_DEPENDENCY'}
      />
    </div>
  );
};
