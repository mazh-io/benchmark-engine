import {
  lemonSqueezySetup,
  createCheckout,
  getSubscription,
} from '@lemonsqueezy/lemonsqueezy.js';

/**
 * Server-only Lemon Squeezy helpers.
 *
 * Call initLS() at the top of every API route that uses the SDK.
 * The SDK stores the key in module scope; repeated calls are safe.
 */

export function initLS() {
  const key = process.env.LEMONSQUEEZY_API_KEY;
  if (!key) throw new Error('Missing LEMONSQUEEZY_API_KEY');
  lemonSqueezySetup({ apiKey: key });
}

export function getStoreId(): string {
  const id = process.env.LEMONSQUEEZY_STORE_ID;
  if (!id) throw new Error('Missing LEMONSQUEEZY_STORE_ID');
  return id;
}

export function getVariantId(): string {
  const id = process.env.LEMONSQUEEZY_VARIANT_ID;
  if (!id) throw new Error('Missing LEMONSQUEEZY_VARIANT_ID');
  return id;
}

export { createCheckout, getSubscription };
