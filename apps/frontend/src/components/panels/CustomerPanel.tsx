import React from 'react';
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
