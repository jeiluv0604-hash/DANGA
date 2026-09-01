import React from 'react';
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
