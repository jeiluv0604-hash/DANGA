import React, { useEffect, useState } from 'react';
import { Building2, CheckSquare, ChefHat, CircleDollarSign, ClipboardCheck, ShieldCheck } from 'lucide-react';

import { getManagementPrototype } from '../../api/management';
import { ManagementPrototype } from '../../types/management';

const won = (value: number) => `${new Intl.NumberFormat('ko-KR').format(value)}원`;
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

const panelStyle: React.CSSProperties = {
  background: '#131b2e', border: '1px solid #23314e', borderRadius: '12px', padding: '18px',
};
const badgeStyle: React.CSSProperties = {
  display: 'inline-flex', padding: '4px 8px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
};

export const ManagementSystemSection: React.FC = () => {
  const [data, setData] = useState<ManagementPrototype | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    getManagementPrototype().then((response) => mounted && setData(response)).catch((reason: Error) => mounted && setError(reason.message));
    return () => { mounted = false; };
  }, []);

  if (error) return <section style={{ ...panelStyle, color: '#fca5a5' }}>경영체계 프로토타입을 불러오지 못했습니다: {error}</section>;
  if (!data) return <section style={panelStyle}>담가화로구이 경영체계 프로토타입을 불러오는 중입니다.</section>;

  const latest = data.finance.monthly_pnl[data.finance.monthly_pnl.length - 1];
  const latestCash = data.finance.cash_flow[data.finance.cash_flow.length - 1];
  const latestBudget = data.finance.budget_actual[data.finance.budget_actual.length - 1];

  return (
    <section style={{ marginTop: '28px' }} data-testid="management-system-prototype">
      <div style={{ ...panelStyle, background: 'linear-gradient(135deg, #102448 0%, #131b2e 70%)', marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '9px', marginBottom: '6px' }}><Building2 size={22} color="#38bdf8" /><h2 style={{ fontSize: '20px' }}>담가화로구이 경영체계 프로토타입</h2></div>
            <p style={{ color: '#94a3b8', fontSize: '13px' }}>매출보다 시스템 · 실제 사용 전 폐쇄 루프 검증</p>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ ...badgeStyle, color: '#fde68a', background: '#78350f' }}>{data.data_disclosure}</span>
            <span style={{ ...badgeStyle, color: '#c4b5fd', background: '#312e81' }}>{data.policy_status}</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        {([['월 매출', won(latest.sales)], ['영업이익', won(latest.operating_profit)], ['영업이익률', percent(latest.operating_margin)], ['기말 현금', won(latestCash.ending_cash)]] as Array<[string, string]>).map(([label, value]) => (
          <div key={label} style={panelStyle}><div style={{ color: '#94a3b8', fontSize: '12px' }}>{latest.period} · {label}</div><div style={{ fontSize: '21px', fontWeight: 800, marginTop: '5px' }}>{value}</div></div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '16px', marginBottom: '16px' }}>
        <div style={panelStyle}>
          <h3 style={{ fontSize: '15px', marginBottom: '10px' }}>매일 기록하는 10개 KPI</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '6px' }}>
            {data.daily_kpi_snapshot.map((kpi) => <div key={kpi.order} style={{ borderTop: '1px solid #23314e', padding: '6px 0', fontSize: '12px', display: 'flex', justifyContent: 'space-between', gap: '8px' }}><span><strong style={{ color: '#38bdf8' }}>{kpi.order}</strong> {kpi.name}</span><span style={{ color: '#6ee7b7', textAlign: 'right' }}>{typeof kpi.value === 'number' ? new Intl.NumberFormat('ko-KR').format(kpi.value) : Object.values(kpi.value).join(' / ')}</span></div>)}
          </div>
        </div>
        <div style={panelStyle}>
          <h3 style={{ fontSize: '15px', marginBottom: '10px' }}>Budget vs Actual · Cash Flow</h3>
          {Object.entries(latestBudget.metrics).map(([metric, values]) => <div key={metric} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', borderTop: '1px solid #23314e', padding: '6px 0', fontSize: '11px' }}><strong>{metric}</strong><span>실적 {won(values.actual)}</span><span style={{ color: values.variance >= 0 ? '#6ee7b7' : '#fca5a5' }}>차이 {won(values.variance)}</span></div>)}
          <div style={{ borderTop: '1px solid #23314e', marginTop: '6px', paddingTop: '8px', color: '#cbd5e1', fontSize: '11px' }}>기초 {won(latestCash.beginning_cash)} + 유입 {won(latestCash.cash_inflows)} - 유출 {won(latestCash.cash_outflows)} = 기말 {won(latestCash.ending_cash)}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(430px, 1fr))', gap: '16px' }}>
        <div style={panelStyle}>
          <h3 style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px', fontSize: '15px' }}><CircleDollarSign size={18} color="#10b981" /> 월 손익·현금흐름</h3>
          <div style={{ overflowX: 'auto' }}><table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead><tr style={{ color: '#94a3b8' }}><th>월</th><th>매출</th><th>식재료</th><th>인건비</th><th>영업이익</th><th>이익률</th></tr></thead>
            <tbody>{data.finance.monthly_pnl.map((item) => <tr key={item.period} style={{ borderTop: '1px solid #23314e', textAlign: 'right' }}><td style={{ padding: '8px', textAlign: 'left' }}>{item.period}</td><td>{won(item.sales)}</td><td>{won(item.food_cost)}</td><td>{won(item.labor_cost)}</td><td style={{ color: '#6ee7b7', fontWeight: 700 }}>{won(item.operating_profit)}</td><td>{percent(item.operating_margin)}</td></tr>)}</tbody>
          </table></div>
          <p style={{ color: '#a78bfa', fontSize: '11px', marginTop: '10px' }}>비용 계정·부문별 배부 기준: {data.finance.allocation_policy_status}</p>
        </div>

        <div style={panelStyle}>
          <h3 style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px', fontSize: '15px' }}><ChefHat size={18} color="#f59e0b" /> Recipe/BOM · 메뉴 ABCD</h3>
          <div style={{ overflowX: 'auto' }}><table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead><tr style={{ color: '#94a3b8' }}><th>등급</th><th>메뉴</th><th>판매가</th><th>표준원가</th><th>공헌이익</th></tr></thead>
            <tbody>{data.menu_engineering.menus.map((menu) => <tr key={menu.menu_id} style={{ borderTop: '1px solid #23314e' }}><td style={{ padding: '8px' }}><span style={{ ...badgeStyle, color: '#fff', background: menu.abcd_class === 'A' ? '#047857' : menu.abcd_class === 'B' ? '#b45309' : menu.abcd_class === 'C' ? '#1d4ed8' : '#b91c1c' }}>{menu.abcd_class}</span></td><td>{menu.menu_name}</td><td>{won(menu.net_price)}</td><td>{won(menu.standard_cost)}</td><td>{won(menu.unit_contribution)}</td></tr>)}</tbody>
          </table></div>
          <p style={{ color: '#a78bfa', fontSize: '11px', marginTop: '10px' }}>ABCD 판정 기준: {data.menu_engineering.policy.status}</p>
        </div>

        <div style={panelStyle}>
          <h3 style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px', fontSize: '15px' }}><ShieldCheck size={18} color="#38bdf8" /> 조직·총괄점장 Scorecard</h3>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>{data.organization.roles.map((role) => <span key={role.role_id} style={{ ...badgeStyle, color: '#bae6fd', background: '#0c4a6e' }}>{role.name}</span>)}</div>
          {data.organization.manager_scorecard.map((metric) => <div key={metric.metric} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderTop: '1px solid #23314e', fontSize: '12px' }}><span>{metric.metric}</span><strong>{metric.weight}%</strong></div>)}
          <p style={{ color: '#a78bfa', fontSize: '11px', marginTop: '10px' }}>가중치: {data.organization.scorecard_policy_status} · 자동 인사결정 없음</p>
          <div style={{ marginTop: '10px', color: '#94a3b8', fontSize: '11px' }}>RACI·전결규정: {data.organization.raci_assignments?.length ?? 0}개 프로세스 · 이중승인·본인승인 금지 · {data.policy_status}</div>
        </div>

        <div style={panelStyle}>
          <h3 style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px', fontSize: '15px' }}><ClipboardCheck size={18} color="#f97316" /> SOP · Action Closure</h3>
          {data.standards.actions.map((action) => <div key={action.action_id} style={{ padding: '9px 0', borderTop: '1px solid #23314e' }}><div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}><strong style={{ fontSize: '12px' }}>{action.title}</strong><span style={{ ...badgeStyle, color: '#fed7aa', background: '#7c2d12' }}>{action.status}</span></div><div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '4px' }}>{action.source_rule_id} → {action.sop_id} · {action.owner_role} · {action.due_date}</div></div>)}
          <div style={{ marginTop: '12px', color: '#94a3b8', fontSize: '11px', display: 'flex', gap: '5px', alignItems: 'center' }}><CheckSquare size={14} /> OPEN → IN_PROGRESS → CLOSED → VERIFIED · 자동 실행 없음</div>
          <div style={{ marginTop: '12px' }}>{data.standards.sops.map((sop) => <details key={sop.sop_id} style={{ borderTop: '1px solid #23314e', padding: '7px 0', fontSize: '11px' }}><summary style={{ cursor: 'pointer', fontWeight: 700 }}>{sop.sop_id} · {sop.title}</summary><div style={{ color: '#94a3b8', marginTop: '5px' }}>{sop.checklist.join(' → ')}</div></details>)}</div>
        </div>
      </div>

      <div style={{ ...panelStyle, marginTop: '16px' }}>
        <h3 style={{ marginBottom: '10px', fontSize: '15px' }}>월간 경영회의 · {data.monthly_review.period}</h3>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '10px' }}><span style={{ ...badgeStyle, color: '#fde68a', background: '#78350f' }}>{data.monthly_review.status}</span><span style={{ ...badgeStyle, color: '#bfdbfe', background: '#1e3a8a' }}>사람 승인 필수</span></div>
        <div style={{ color: '#cbd5e1', fontSize: '12px' }}>다음 달 Top Actions: {data.monthly_review.top_actions.join(' · ')}</div>
        {data.monthly_review.management_brief && <div style={{ marginTop: '10px', padding: '10px', borderRadius: '8px', background: '#0b1120', color: '#cbd5e1', fontSize: '12px' }}><strong>AI Management Brief · {data.monthly_review.management_brief.provider}</strong><div style={{ marginTop: '5px' }}>{data.monthly_review.management_brief.executive_summary}</div></div>}
      </div>
    </section>
  );
};
