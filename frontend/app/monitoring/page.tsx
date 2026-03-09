'use client';

import { Suspense } from 'react';
import { MonitoringDashboard } from '@/templates/monitoring/MonitoringDashboard';

export default function MonitoringPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black flex items-center justify-center">
          <span className="text-white/60 text-sm">Loading...</span>
        </div>
      }
    >
      <div className="min-h-screen bg-black">
        <div className="px-4 pt-8 pb-6 max-w-[1400px] mx-auto">
          <MonitoringDashboard />
        </div>
      </div>
    </Suspense>
  );
}
