'use client';

import { useState } from 'react';
import { Header } from '@/layout/Header';
import { useBenchmarkData } from '@/hooks/useBenchmarkData';
import { useDashboardMetrics } from '@/hooks/useDashboardMetric';
import { StatsHighlightsGrid } from '@/templates/stats/StatsHighlightsGrid';
import { FilterBar } from '@/templates/filters/FilterBar';
import { IndexTable } from '@/templates/IndexTable/IndexTable';
import { MainNav, type Tab } from '@/templates/navigation/MainNav';
import { InsightsGrid } from '@/templates/insights/InsightsGrid';
import { InsightsToolbar } from '@/templates/insights/InsightsToolbar';
import { InsightsFooter } from '@/templates/insights/InsightsFooter';
import { IndexFooter } from '@/layout/IndexFooter';
import { APIPage } from '@/templates/api/APIPage';
import type { TimeFilter } from '@/api/types';

export default function DashboardPage() {
  const [expandedCard, setExpandedCard] = useState<
    'fastest' | 'slowest' | 'bestvalue' | 'moststable' | 'insight' | null
  >(null);
  const [activeTab, setActiveTab] = useState<Tab>('grid');
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('24h');

  const { data, isLoading, error, refetch } = useBenchmarkData({
    timeRange: timeFilter,
    autoRefresh: timeFilter === 'live',
  });

  const dashboard = useDashboardMetrics(data);

  const handleTimeChange = (time: TimeFilter) => {
    setTimeFilter(time);
  };

  if (isLoading) {
    return <div className="min-h-screen bg-black text-white p-10">Loading…</div>;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <button onClick={() => refetch()} className="text-white">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black">
      <Header />

      {/* Divider */}
      <div className="h-px bg-[#0f0f0f]" />

      <div className="px-4 pt-6 pb-4">
        <StatsHighlightsGrid
          expandedCard={expandedCard}
          setExpandedCard={setExpandedCard}
          topSpeed={dashboard.topSpeed}
          slowestSpeed={dashboard.slowestSpeed}
          top5Fastest={dashboard.top5Fastest}
          bottom5Slowest={dashboard.bottom5Slowest}
          top5BestValue={dashboard.top5BestValue}
          top5MostStable={dashboard.top5MostStable}
          results={data?.results}
        />
      </div>

      <MainNav activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="px-4 pt-4 pb-6">
        {activeTab === 'grid' && (
          <>
            <FilterBar
              totalProviders={data?.results?.length ?? 0}
              providerChips={dashboard.providerChips}
              selectedTime={timeFilter}
              onTimeChange={handleTimeChange}
            />

            <IndexTable
              results={data?.results ?? []}
              metrics={data?.metrics ?? new Map()}
            />

            <IndexFooter />
          </>
        )}

        {activeTab === 'insights' && (
          <>
            <InsightsToolbar 
              selectedTime={timeFilter}
              onTimeChange={handleTimeChange} 
            />
            <InsightsGrid
              results={data?.results}
              metrics={data?.metrics}
            />
            <InsightsFooter />
          </>
        )}

        {activeTab === 'api' && (
          <>
            <APIPage />
            <IndexFooter />
          </>
        )}
      </main>
    </div>
  );
}
