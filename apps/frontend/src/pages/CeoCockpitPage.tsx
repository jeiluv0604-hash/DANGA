import React, { useState } from 'react';
import { AlertTriangle, CalendarDays, CalendarRange, ChartNoAxesCombined, MessageCircleMore, PackageSearch, type LucideIcon } from 'lucide-react';

import { AlertPriorityPanel } from '../components/alerts/AlertPriorityPanel';
import { AnalystBriefingSection } from '../components/analyst/AnalystBriefingSection';
import { TrendCharts } from '../components/charts/TrendCharts';
import { ErrorState } from '../components/common/ErrorState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EvidenceDrawer } from '../components/evidence/EvidenceDrawer';
import { KpiGrid } from '../components/kpi/KpiGrid';
import { KpiHeroCard } from '../components/kpi/KpiHeroCard';
import { DataIncompleteBanner } from '../components/layout/DataIncompleteBanner';
import { Header } from '../components/layout/Header';
import { ManagementSystemSection } from '../components/management/ManagementSystemSection';
import { CustomerPanel } from '../components/panels/CustomerPanel';
import { InventoryPanel } from '../components/panels/InventoryPanel';
import { SummarySection } from '../components/summary/SummarySection';
import { useDailyDashboard } from '../hooks/useDailyDashboard';
import { useRecentTrends } from '../hooks/useRecentTrends';
import { useSummary } from '../hooks/useSummary';
import { formatWon } from '../utils/formatters';

type DashboardTab = 'trend' | 'monthly' | 'yearly' | 'alerts' | 'inventory' | 'customer';

const tabs: Array<{ id: DashboardTab; label: string; icon: LucideIcon }> = [
  { id: 'trend', label: '오늘 및 최근 7일 경영 추세', icon: ChartNoAxesCombined },
  { id: 'monthly', label: '월 단위 매출 정보', icon: CalendarDays },
  { id: 'yearly', label: '연 단위 매출정보', icon: CalendarRange },
  { id: 'alerts', label: '오늘의 경영이상 정보', icon: AlertTriangle },
  { id: 'inventory', label: '식재료 재고 및 폐기상태', icon: PackageSearch },
  { id: 'customer', label: '고객 반응 및 서비스 품질', icon: MessageCircleMore },
];

export const CeoCockpitPage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState('2026-08-31');
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<DashboardTab>('trend');

  const { data: dailyData, loading: dailyLoading, error: dailyError, refetch: refetchDaily } = useDailyDashboard(selectedDate);
  const { facts: trendFacts } = useRecentTrends(selectedDate);
  const { summary: summaryData } = useSummary();

  const renderTabContent = () => {
    if (!dailyData) return null;
    switch (activeTab) {
      case 'monthly': return <ManagementSystemSection view="monthly" />;
      case 'yearly': return <><ManagementSystemSection view="yearly" />{summaryData && <SummarySection summary={summaryData} />}</>;
      case 'alerts': return <AlertPriorityPanel alerts={dailyData.alerts} onOpenEvidence={(id) => setActiveEvidenceId(id)} />;
      case 'inventory': return <div style={{ maxWidth: '760px' }}><InventoryPanel kpis={dailyData.kpis} kpiStatus={dailyData.kpi_status} alerts={dailyData.alerts} /></div>;
      case 'customer': return <div style={{ maxWidth: '760px' }}><CustomerPanel kpis={dailyData.kpis} kpiStatus={dailyData.kpi_status} alerts={dailyData.alerts} /></div>;
      default: return <><KpiGrid kpis={dailyData.kpis} kpiStatus={dailyData.kpi_status} alerts={dailyData.alerts} includeSales={false} /><TrendCharts facts={trendFacts} /></>;
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#090d16', color: '#f8fafc' }}>
      <Header currentDate={selectedDate} onDateChange={setSelectedDate} />
      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
        {dailyLoading ? <LoadingSkeleton /> : dailyError ? <ErrorState message={dailyError} onRetry={refetchDaily} /> : dailyData ? (
          <div>
            {dailyData.data_status === 'DATA_INCOMPLETE' && <DataIncompleteBanner date={dailyData.date} />}

            <section aria-label="오늘 매출" style={{ marginBottom: '20px' }}>
              <div style={{ marginBottom: '10px' }}><h1 style={{ fontSize: '18px' }}>오늘 매출</h1><p style={{ color: '#94a3b8', fontSize: '12px' }}>{selectedDate} · 가장 먼저 확인하는 핵심 지표</p></div>
              <div style={{ maxWidth: '100%', display: 'grid', gridTemplateColumns: 'minmax(260px, 1fr)' }}>
                <KpiHeroCard title="오늘 매출 (Sales)" primaryValue={formatWon(dailyData.kpis.sales, dailyData.kpi_status.sales)} subValue={`고객 ${dailyData.kpis.guests !== null ? `${dailyData.kpis.guests}명` : '데이터 없음'}`} secondaryText={`객단가 ${formatWon(dailyData.kpis.avg_check, dailyData.kpi_status.avg_check)}`} />
              </div>
            </section>

            <nav aria-label="경영 대시보드 메뉴" role="tablist" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '8px', marginBottom: '16px' }}>
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const selected = activeTab === tab.id;
                return <button key={tab.id} type="button" role="tab" aria-selected={selected} aria-controls={`panel-${tab.id}`} onClick={() => setActiveTab(tab.id)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '7px', minHeight: '48px', padding: '9px 12px', borderRadius: '9px', border: `1px solid ${selected ? '#38bdf8' : '#23314e'}`, background: selected ? '#0c4a6e' : '#131b2e', color: selected ? '#e0f2fe' : '#94a3b8', fontSize: '12px', fontWeight: selected ? 800 : 600, transition: 'all 150ms ease' }}><Icon size={16} />{tab.label}</button>;
              })}
            </nav>

            <section id={`panel-${activeTab}`} role="tabpanel" aria-live="polite" style={{ minHeight: '360px', marginBottom: '28px' }}>{renderTabContent()}</section>

            <AnalystBriefingSection date={selectedDate} onOpenEvidence={(id) => setActiveEvidenceId(id)} />
          </div>
        ) : null}
      </main>
      <EvidenceDrawer evidenceId={activeEvidenceId} onClose={() => setActiveEvidenceId(null)} />
    </div>
  );
};
