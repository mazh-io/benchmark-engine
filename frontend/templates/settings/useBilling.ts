'use client';

import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/api/supabase';

export type BillingView = 'loading' | 'free' | 'active' | 'cancelled' | 'past_due' | 'expired';

interface SubscriptionRow {
  product_name: string | null;
  status: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

const BADGES: Record<string, { text: string; cls: string }> = {
  active:    { text: 'ACTIVE',                cls: 'st-billing-badge' },
  cancelled: { text: 'CANCELS AT PERIOD END', cls: 'st-billing-badge st-badge-warn' },
  past_due:  { text: 'PAST DUE',             cls: 'st-billing-badge st-badge-danger' },
  expired:   { text: 'EXPIRED',              cls: 'st-billing-badge st-badge-danger' },
};

export function useBilling() {
  const [view, setView] = useState<BillingView>('loading');
  const [sub, setSub] = useState<SubscriptionRow | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const { data } = await (supabase as import('@supabase/supabase-js').SupabaseClient)
        .from('subscriptions')
        .select('product_name, status, current_period_end, cancel_at_period_end')
        .maybeSingle<SubscriptionRow>();

      if (!data) { setView('free'); return; }

      setSub(data);
      if (data.status === 'expired') setView('expired');
      else if (data.cancel_at_period_end) setView('cancelled');
      else setView(data.status as BillingView);
    })();
  }, []);

  const callApi = useCallback(async (path: string, method = 'GET') => {
    setError(null);
    setBusy(true);
    try {
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;
      if (!token) { setError('Not logged in'); return; }

      const res = await fetch(path, { method, headers: { Authorization: `Bearer ${token}` } });
      const body = await res.json();
      if (!res.ok) { setError(body.error ?? `Request failed (${res.status})`); return; }
      window.location.href = body.url;
    } catch {
      setError('Something went wrong');
    } finally {
      setBusy(false);
    }
  }, []);

  const planName = sub?.product_name ?? 'Pro';
  const badge = BADGES[view];
  const periodEnd = sub?.current_period_end
    ? new Date(sub.current_period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : null;

  return {
    view,
    planName,
    badge,
    periodEnd,
    busy,
    error,
    checkout: () => callApi('/api/billing/checkout', 'POST'),
    portal:   () => callApi('/api/billing/portal'),
  };
}
