import { createClient, type SupabaseClient } from '@supabase/supabase-js';

/**
 * Server-only Supabase client with service-role privileges.
 *
 * Never import this from client components — the service-role key
 * must stay on the server.
 */

let _admin: SupabaseClient | null = null;

export function getAdminClient(): SupabaseClient {
  if (_admin) return _admin;

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !key) {
    throw new Error(
      'Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY — cannot create admin client',
    );
  }

  _admin = createClient(url, key, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  return _admin;
}
