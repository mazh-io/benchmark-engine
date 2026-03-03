'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/layout/Header';
import { useAuth } from '@/contexts/AuthContext';
import { MainNav } from '@/layout/MainNav';
import { IndexFooter } from '@/layout/IndexFooter';
import { useBenchmarkData } from '@/hooks/useBenchmarkData';
import { useDashboardMetrics } from '@/hooks/useDashboardMetric';
import { HighlightsGrid } from '@/templates/highlights/HighlightsGrid';
import { PricingCard } from '@/templates/early-access/PricingCard';
import { FeatureHighlights } from '@/templates/early-access/FeatureHighlights';
import { CredibilityStats } from '@/templates/early-access/CredibilityStats';
import { FeatureTable } from '@/templates/early-access/FeatureTable';
import { FAQSection } from '@/templates/early-access/FAQSection';
import { CTASection } from '@/templates/early-access/CTASection';

export default function EarlyAccessPage() {
  const router = useRouter();
  const { isLoggedIn, user } = useAuth();
  const handleTabChange = useCallback((tab: 'grid' | 'insights' | 'api') => {
    if (tab === 'grid') router.push('/');
    if (tab === 'insights') router.push('/?tab=insights');
    if (tab === 'api') router.push('/?tab=api');
  }, [router]);
  const [expandedCard, setExpandedCard] = useState<
    'fastest' | 'slowest' | 'bestvalue' | 'moststable' | 'insight' | null
  >(null);

  const { data } = useBenchmarkData({ timeRange: '24h', autoRefresh: false });
  const dashboard = useDashboardMetrics(data);

  return (
    <div className="min-h-screen bg-black" style={{ fontFamily: 'var(--font-space), system-ui, sans-serif' }}>
      {/* Dashboard chrome */}
      <Header tier={isLoggedIn ? 'free' : 'logged-out'} user={user ?? undefined} />
      <div className="h-px bg-[#0f0f0f]" />

      <div className="px-4 pt-6 pb-4">
        <HighlightsGrid
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

      <MainNav activeTab={null} onTabChange={handleTabChange} />

      {/* Page content */}
      <div className="ea-content">
        <section className="ea-hero">
          <div className="ea-badge">Founding Member Pricing</div>
          <h1 className="ea-title">Early Pro Access</h1>
          <p className="ea-subtitle">
            Lock in the founding member rate forever.<br />
            Full access to all Pro features—current and upcoming.
          </p>
        </section>

        <PricingCard />
        <FeatureHighlights />
        <CredibilityStats data={data} />
        <FeatureTable />
        <FAQSection />
        <CTASection />
      </div>

      <IndexFooter />
    </div>
  );
}
