export interface RuleMeta {
  name: string;
  description: string;
  category: 'LABOR' | 'COST' | 'INVENTORY' | 'CUSTOMER' | 'DATA_QUALITY' | 'PROFIT';
}

export const RULE_REGISTRY: Record<string, RuleMeta> = {
  'R-LAB-01': {
    name: '인건비율 기준 초과',
    description: '일일 인건비율이 관리 기준(33.0%)을 초과했습니다.',
    category: 'LABOR',
  },
  'R-INV-01': {
    name: '재고 차이 확인 필요',
    description: '실사 재고와 이론 재고 간 차이가 관리 기준(-5.0kg) 이하로 발생하여 실사 확인이 필요합니다.',
    category: 'INVENTORY',
  },
  'R-FC-01': {
    name: '식재료 원가율 기준 초과',
    description: '일일 식재료 원가율이 관리 기준(39.0%)을 초과했습니다.',
    category: 'COST',
  },
  'R-FC-01-PERIOD': {
    name: '식재료 원가율 지속 상승',
    description: '최근 7일 이상 연속으로 원가율이 39.0% 이상 유지되고 있습니다.',
    category: 'COST',
  },
  'R-WST-01': {
    name: '폐기율 기준 초과',
    description: '판매량 대비 식재료 폐기율이 관리 기준(5.0%)을 초과했습니다.',
    category: 'INVENTORY',
  },
  'R-CUS-01': {
    name: '고객경험 확인 필요',
    description: '고객 불만 접수(5건 이상) 또는 고객 평점(4.2 미만) 이상이 감지되었습니다.',
    category: 'CUSTOMER',
  },
  'R-PRO-01': {
    name: '매출 증가 대비 수익성 악화',
    description: '매출은 증가했으나 공헌이익률이 하락하여 수익성 역행이 발생했습니다.',
    category: 'PROFIT',
  },
  'R-DQ-01': {
    name: '필수 데이터 누락',
    description: '일일 필수 입력 필드가 누락되어 일부 지표 계산 및 자동 분석이 차단되었습니다.',
    category: 'DATA_QUALITY',
  },
};

export function getRuleMeta(ruleId: string): RuleMeta {
  return (
    RULE_REGISTRY[ruleId] || {
      name: ruleId,
      description: '운영 이상이 감지되었습니다.',
      category: 'DATA_QUALITY',
    }
  );
}
