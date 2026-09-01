import React from 'react';
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
