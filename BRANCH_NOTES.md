# feat/lemonsqueezy-billing

## SQ / Shqip

### Pershkrim

Kjo branch implementon integrimin e plote te Lemon Squeezy per pagesa (subscriptions) dhe fikson bugun e fshirjes se account-it (401 error).

### Cka u be

**Fshirja e account-it (fix 401):**
- Krijuar `DELETE /api/account` si Next.js API route ne vend te FastAPI Python endpoint-it qe dshtonte me verify JWT
- Tokeni tash verifikohet permes `admin.auth.getUser(token)` (Supabase vet e ben, nuk ka nevoj per `SUPABASE_JWT_SECRET`)
- Soft-delete (`is_active = false`) + hard-delete (`deleteUser`) behet krejt server-side

**Billing (Lemon Squeezy):**
- Tabele e re `subscriptions` ne Supabase me RLS (useri lexon vetem te veten, shkrimet behen server-side permes webhook)
- 3 API route te reja:
  - `POST /api/billing/checkout` -- krijon checkout session ne LS, kthen URL
  - `POST /api/billing/webhook` -- pranon events nga LS (subscription_created, cancelled, expired, etj.), verifikon HMAC signature, upsert ne DB
  - `GET /api/billing/portal` -- kthen URL per LS customer portal (manage payment, cancel, invoices)
- BillingSection i ri plotesisht dinamik -- zero hardcoded data, gjithcka vjen nga DB ose env vars
- CSS e pastruar -- larguar klasa te vdekura per mock invoices/payment method

**Infrastrukture:**
- `api/supabase-admin.ts` -- Supabase admin client (server-only, singleton, reusable)
- `api/lemonsqueezy.ts` -- LS SDK helpers (server-only)
- `api/server-auth.ts` -- shared auth helper per te 4 routet (1 pattern, jo 3 te ndryshme)
- `@lemonsqueezy/lemonsqueezy.js` shtuar si dependency

### Env vars te reja (vendos ne Vercel)

| Variable | Ku | Pershkrim |
|----------|-----|-----------|
| `SUPABASE_SERVICE_ROLE_KEY` | Server | Supabase service role key (jo anon key) |
| `LEMONSQUEEZY_API_KEY` | Server | LS API key (test key per fillim) |
| `LEMONSQUEEZY_WEBHOOK_SECRET` | Server | LS webhook signing secret |
| `LEMONSQUEEZY_STORE_ID` | Server | LS store ID |
| `LEMONSQUEEZY_VARIANT_ID` | Server | LS variant ID per Pro Monthly |
| `NEXT_PUBLIC_PRO_LABEL` | Public | Tekst per CTA button (psh. "Pro — €19/mo") |

### Hapa per test

1. Krijo account ne [app.lemonsqueezy.com](https://app.lemonsqueezy.com)
2. Krijo Store + Product (Pro Plan, €19/mo recurring)
3. Aktivizo Test Mode
4. Krijo API key + Webhook pointing te `/api/billing/webhook`
5. Vendos env vars ne Vercel
6. Ekzekuto migration `004_subscriptions.sql` ne Supabase
7. Test: kliko "Get Pro" -> paguan me karte fake `4242 4242 4242 4242` -> webhook update -> billing tab shfaq subscription

---

## EN / English

### Summary

This branch implements the full Lemon Squeezy billing integration (subscriptions) and fixes the account deletion 401 error.

### What changed

**Account deletion (fix 401):**
- Created `DELETE /api/account` as a Next.js API route instead of the failing FastAPI Python endpoint
- Token verification now uses `admin.auth.getUser(token)` (Supabase native, no `SUPABASE_JWT_SECRET` required)
- Both soft-delete (`is_active = false`) and hard-delete (`deleteUser`) happen server-side

**Billing (Lemon Squeezy):**
- New `subscriptions` table in Supabase with RLS (users read their own row, writes happen server-side via webhook)
- 3 new API routes:
  - `POST /api/billing/checkout` -- creates an LS checkout session, returns URL
  - `POST /api/billing/webhook` -- receives LS events (subscription_created, cancelled, expired, etc.), verifies HMAC signature, upserts to DB
  - `GET /api/billing/portal` -- returns the LS customer portal URL (manage payment, cancel, invoices)
- BillingSection fully rewritten -- zero hardcoded data, everything comes from DB or env vars
- Cleaned up dead CSS for removed mock invoice/payment sections

**Infrastructure:**
- `api/supabase-admin.ts` -- Supabase admin client (server-only, singleton, reusable)
- `api/lemonsqueezy.ts` -- LS SDK helpers (server-only)
- `api/server-auth.ts` -- shared auth helper across all 4 routes (single pattern, replaces 3 different implementations)
- Added `@lemonsqueezy/lemonsqueezy.js` dependency

### New env vars (set in Vercel)

| Variable | Scope | Description |
|----------|-------|-------------|
| `SUPABASE_SERVICE_ROLE_KEY` | Server | Supabase service role key (not the anon key) |
| `LEMONSQUEEZY_API_KEY` | Server | LS API key (use test key initially) |
| `LEMONSQUEEZY_WEBHOOK_SECRET` | Server | LS webhook signing secret |
| `LEMONSQUEEZY_STORE_ID` | Server | LS store ID |
| `LEMONSQUEEZY_VARIANT_ID` | Server | LS variant ID for Pro Monthly |
| `NEXT_PUBLIC_PRO_LABEL` | Public | CTA button text (e.g. "Pro — €19/mo") |

### Test steps

1. Create account at [app.lemonsqueezy.com](https://app.lemonsqueezy.com)
2. Create Store + Product (Pro Plan, €19/mo recurring)
3. Enable Test Mode
4. Create API key + Webhook pointing to `/api/billing/webhook`
5. Set env vars in Vercel
6. Run migration `004_subscriptions.sql` in Supabase
7. Test: click "Get Pro" -> pay with test card `4242 4242 4242 4242` -> webhook fires -> billing tab shows subscription

### Files changed

**New files:**

| File | Purpose |
|------|---------|
| `frontend/api/supabase-admin.ts` | Server-only Supabase admin client |
| `frontend/api/lemonsqueezy.ts` | Server-only LS SDK helpers |
| `frontend/api/server-auth.ts` | Shared request authentication |
| `frontend/app/api/account/route.ts` | `DELETE /api/account` |
| `frontend/app/api/billing/checkout/route.ts` | `POST /api/billing/checkout` |
| `frontend/app/api/billing/webhook/route.ts` | `POST /api/billing/webhook` |
| `frontend/app/api/billing/portal/route.ts` | `GET /api/billing/portal` |
| `backend/migrations/004_subscriptions.sql` | Subscriptions table migration |

**Modified files:**

| File | Change |
|------|--------|
| `backend/schema.sql` | Added subscriptions table + indexes |
| `frontend/api/database.types.ts` | Added subscriptions type |
| `frontend/.env.local.example` | Added LS + pro label env vars |
| `frontend/data/early-access.ts` | Documented dual checkout flows |
| `frontend/package.json` | Added `@lemonsqueezy/lemonsqueezy.js` |
| `frontend/styles/components/settings.css` | Added badge variants, removed dead invoice/payment CSS |
| `frontend/templates/settings/BillingSection.tsx` | Full rewrite: dynamic data, sub-components, no hardcoded values |
| `frontend/templates/settings/useAccountSection.ts` | Simplified delete flow to use new API route |
