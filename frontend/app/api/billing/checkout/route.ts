import { NextRequest, NextResponse } from 'next/server';
import { authenticateRequest } from '@/lib/server-auth';
import { initLS, createCheckout, getStoreId, getVariantId } from '@/lib/lemonsqueezy';

export const runtime = 'nodejs';

/**
 * POST /api/billing/checkout
 *
 * Creates a Lemon Squeezy checkout session for the authenticated user
 * and returns the hosted checkout URL.
 */
export async function POST(req: NextRequest) {
  const auth = await authenticateRequest(req);
  if (auth.error) return auth.error;

  try {
    initLS();
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : 'Billing not configured' },
      { status: 503 },
    );
  }

  const { data: checkout, error: lsErr } = await createCheckout(
    getStoreId(),
    getVariantId(),
    {
      checkoutData: {
        email: auth.user.email ?? undefined,
        custom: { user_id: auth.user.id },
      },
      productOptions: { redirectUrl: `${requestOrigin(req)}/settings#billing` },
    },
  );

  if (lsErr) {
    return NextResponse.json(
      { error: lsErr.message ?? 'Failed to create checkout' },
      { status: 502 },
    );
  }

  const url = checkout?.data?.attributes?.url;
  if (!url) {
    return NextResponse.json({ error: 'No checkout URL returned' }, { status: 502 });
  }

  return NextResponse.json({ url });
}

function requestOrigin(req: NextRequest): string {
  const host = req.headers.get('host') ?? 'localhost:3000';
  const proto = req.headers.get('x-forwarded-proto') ?? 'https';
  return `${proto}://${host}`;
}
