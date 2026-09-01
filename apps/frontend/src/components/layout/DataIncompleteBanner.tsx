import React from 'react';

interface DataIncompleteBannerProps {
  date: string;
}

export const DataIncompleteBanner: React.FC<DataIncompleteBannerProps> = ({ date }) => {
  return (
    <div
      data-testid="data-incomplete-banner"
      style={{
        backgroundColor: '#450a0a',
        border: '1px solid #dc2626',
        borderRadius: '8px',
        padding: '14px 18px',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
      }}
    >
      <span style={{ fontSize: '20px' }}>⚠️</span>
      <div>
        <h4 style={{ color: '#fecaca', fontSize: '15px', fontWeight: 'bold', margin: '0 0 4px 0' }}>
          일부 필수 데이터가 누락되었습니다 ({date})
        </h4>
        <p style={{ color: '#fca5a5', fontSize: '13px', margin: 0, lineHeight: 1.4 }}>
          Food Cost 데이터가 입력되지 않아 <strong>식재료 원가율</strong> 및 <strong>영업이익</strong>을 계산할 수 없습니다 (계산 불가 표기).
          <br />
          매출·객수·인건비·재고·고객 평점 등 <strong>독립 관측치</strong>는 신뢰성 있게 정상 보존되어 표시됩니다.
        </p>
      </div>
    </div>
  );
};
