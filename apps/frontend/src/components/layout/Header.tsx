import React from 'react';
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
