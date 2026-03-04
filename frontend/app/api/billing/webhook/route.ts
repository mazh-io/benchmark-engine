import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';
import { getAdminClient } from '@/lib/supabase-admin';

export const runtime = 'nodejs';

/**
 * POST /api/billing/webhook
 *
 * Receives Lemon Squeezy webhook events, verifies the HMAC-SHA256
 * signature, and upserts subscription state in Supabase.
 */
export async function POST(req: NextRequest) {
  const secret = process.env.LEMONSQUEEZY_WEBHOOK_SECRET;
  if (!secret) {
    return NextResponse.json({ error: 'Webhook not configured' }, { status: 503 });
  }

  const rawBody = await req.text();
  const signature = req.headers.get('x-signature') ?? '';

  if (!verifySignature(rawBody, signature, secret)) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
  }

  let payload: Record<string, unknown>;
  try {
    payload = JSON.parse(rawBody);
  } catch {
    return NextResponse.json({ error: 'Malformed JSON body' }, { status: 400 });
  }

  const meta = payload.meta as Record<string, unknown> | undefined;
  const data = payload.data as Record<string, unknown> | undefined;
  const attrs = (data?.attributes ?? {}) as Record<string, unknown>;
  const eventName = String(meta?.event_name ?? '');
  const userId = (meta?.custom_data as Record<string, unknown> | undefined)?.user_id as
    | string
    | undefined;

  if (!userId) {
    return NextResponse.json({ error: 'Missing user_id in custom_data' }, { status: 400 });
  }

  const admin = getAdminClient();

  const baseFields = {
    user_id: userId,
    ls_subscription_id: String(data?.id ?? ''),
    ls_customer_id: String(attrs.customer_id ?? ''),
    variant_id: String(attrs.variant_id ?? ''),
    product_name: (attrs.product_name as string) ?? null,
    updated_at: new Date().toISOString(),
  };

  switch (eventName) {
    case 'subscription_created':
    case 'subscription_updated':
    case 'subscription_resumed': {
      const { error } = await admin.from('subscriptions').upsert(
        {
          ...baseFields,
          status: mapStatus(String(attrs.status ?? '')),
          current_period_end: (attrs.renews_at ?? attrs.ends_at ?? null) as string | null,
          cancel_at_period_end: Boolean(attrs.cancelled),
        },
        { onConflict: 'user_id' },
      );
      if (error) {
        console.error('[webhook] upsert failed:', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
      }
      break;
    }

    case 'subscription_cancelled': {
      await admin
        .from('subscriptions')
        .update({
          cancel_at_period_end: true,
          status: mapStatus(String(attrs.status ?? '')),
          updated_at: baseFields.updated_at,
        })
        .eq('user_id', userId);
      break;
    }

    case 'subscription_expired': {
      await admin
        .from('subscriptions')
        .update({ status: 'expired', cancel_at_period_end: false, updated_at: baseFields.updated_at })
        .eq('user_id', userId);
      break;
    }

    case 'subscription_payment_failed': {
      await admin
        .from('subscriptions')
        .update({ status: 'past_due', updated_at: baseFields.updated_at })
        .eq('user_id', userId);
      break;
    }

    case 'subscription_payment_success': {
      await admin
        .from('subscriptions')
        .update({
          status: 'active',
          current_period_end: (attrs.renews_at ?? attrs.ends_at ?? null) as string | null,
          cancel_at_period_end: false,
          updated_at: baseFields.updated_at,
        })
        .eq('user_id', userId);
      break;
    }

    default:
      break;
  }

  return NextResponse.json({ ok: true });
}

function verifySignature(body: string, signature: string, secret: string): boolean {
  const expected = crypto.createHmac('sha256', secret).update(body).digest('hex');
  if (expected.length !== signature.length) return false;
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(signature));
}

function mapStatus(lsStatus: string): string {
  const map: Record<string, string> = {
    active: 'active',
    on_trial: 'active',
    paused: 'paused',
    past_due: 'past_due',
    unpaid: 'past_due',
    cancelled: 'cancelled',
    expired: 'expired',
  };
  return map[lsStatus] ?? lsStatus;
}
