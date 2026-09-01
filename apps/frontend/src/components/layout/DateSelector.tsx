import React from 'react';

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
