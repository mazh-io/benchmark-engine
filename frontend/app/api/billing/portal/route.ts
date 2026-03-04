import { NextRequest, NextResponse } from 'next/server';
import { getAdminClient } from '@/lib/supabase-admin';
import { authenticateRequest } from '@/lib/server-auth';
import { initLS, getSubscription } from '@/lib/lemonsqueezy';

export const runtime = 'nodejs';

/**
 * GET /api/billing/portal
 *
 * Returns the Lemon Squeezy customer portal URL for the authenticated
 * user's subscription. The portal handles payment updates, cancellation,
 * resume, and invoices.
 */
export async function GET(req: NextRequest) {
  const auth = await authenticateRequest(req);
  if (auth.error) return auth.error;

  const admin = getAdminClient();
  const { data: sub } = await admin
    .from('subscriptions')
    .select('ls_subscription_id')
    .eq('user_id', auth.user.id)
    .single();

  if (!sub?.ls_subscription_id) {
    return NextResponse.json({ error: 'No subscription found' }, { status: 404 });
  }

  try {
    initLS();
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : 'Billing not configured' },
      { status: 503 },
    );
  }

  const { data: lsSub, error: lsErr } = await getSubscription(sub.ls_subscription_id);
  if (lsErr || !lsSub) {
    return NextResponse.json(
      { error: lsErr?.message ?? 'Failed to fetch subscription' },
      { status: 502 },
    );
  }

  const portalUrl = lsSub.data?.attributes?.urls?.customer_portal;
  if (!portalUrl) {
    return NextResponse.json({ error: 'Portal URL not available' }, { status: 502 });
  }

  return NextResponse.json({ url: portalUrl });
}
