import React, { useState } from 'react';
import { Header } from '../components/layout/Header';
import { DataIncompleteBanner } from '../components/layout/DataIncompleteBanner';
import { KpiGrid } from '../components/kpi/KpiGrid';
import { AlertPriorityPanel } from '../components/alerts/AlertPriorityPanel';
import { TrendCharts } from '../components/charts/TrendCharts';
import { InventoryPanel } from '../components/panels/InventoryPanel';
import { CustomerPanel } from '../components/panels/CustomerPanel';
import { SummarySection } from '../components/summary/SummarySection';
import { AnalystBriefingSection } from '../components/analyst/AnalystBriefingSection';
import { EvidenceDrawer } from '../components/evidence/EvidenceDrawer';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorState } from '../components/common/ErrorState';
import { useDailyDashboard } from '../hooks/useDailyDashboard';
import { useRecentTrends } from '../hooks/useRecentTrends';
import { useSummary } from '../hooks/useSummary';
import { ManagementSystemSection } from '../components/management/ManagementSystemSection';

export const CeoCockpitPage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>('2026-08-31');
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null);

  const { data: dailyData, loading: dailyLoading, error: dailyError, refetch: refetchDaily } = useDailyDashboard(selectedDate);
  const { facts: trendFacts } = useRecentTrends(selectedDate);
  const { summary: summaryData } = useSummary();

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#090d16', color: '#f8fafc' }}>
      <Header currentDate={selectedDate} onDateChange={setSelectedDate} />

      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
        {dailyLoading ? (
          <LoadingSkeleton />
        ) : dailyError ? (
          <ErrorState message={dailyError} onRetry={refetchDaily} />
        ) : dailyData ? (
          <div>
            {dailyData.data_status === 'DATA_INCOMPLETE' && (
              <DataIncompleteBanner date={dailyData.date} />
            )}

            <AnalystBriefingSection
              date={selectedDate}
              onOpenEvidence={(id) => setActiveEvidenceId(id)}
            />

            <KpiGrid
              kpis={dailyData.kpis}
              kpiStatus={dailyData.kpi_status}
              alerts={dailyData.alerts}
            />

            <TrendCharts facts={trendFacts} />

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '16px',
                marginBottom: '24px',
              }}
            >
              <AlertPriorityPanel
                alerts={dailyData.alerts}
                onOpenEvidence={(id) => setActiveEvidenceId(id)}
              />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <InventoryPanel
                  kpis={dailyData.kpis}
                  kpiStatus={dailyData.kpi_status}
                  alerts={dailyData.alerts}
                />
                <CustomerPanel
                  kpis={dailyData.kpis}
                  kpiStatus={dailyData.kpi_status}
                  alerts={dailyData.alerts}
                />
              </div>
            </div>

            {summaryData && <SummarySection summary={summaryData} />}

            <ManagementSystemSection />
          </div>
        ) : null}
      </main>

      <EvidenceDrawer
        evidenceId={activeEvidenceId}
        onClose={() => setActiveEvidenceId(null)}
      />
    </div>
  );
};
