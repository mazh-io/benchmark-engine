import { NextRequest, NextResponse } from 'next/server';
import type { User } from '@supabase/supabase-js';
import { getAdminClient } from '@/lib/supabase-admin';

type AuthResult =
  | { user: User; error?: never }
  | { user?: never; error: NextResponse };

/**
 * Extracts the Bearer token from the request and verifies it via
 * Supabase admin client. Returns the authenticated User on success
 * or a ready-to-return NextResponse on failure.
 */
export async function authenticateRequest(req: NextRequest): Promise<AuthResult> {
  const header = req.headers.get('authorization');
  if (!header?.startsWith('Bearer ')) {
    return {
      error: NextResponse.json({ error: 'Missing or invalid authorization header' }, { status: 401 }),
    };
  }

  const token = header.slice(7);

  let admin;
  try {
    admin = getAdminClient();
  } catch {
    return {
      error: NextResponse.json({ error: 'Auth service not configured' }, { status: 503 }),
    };
  }

  const { data, error: authErr } = await admin.auth.getUser(token);
  if (authErr || !data.user) {
    return {
      error: NextResponse.json({ error: authErr?.message ?? 'Invalid or expired token' }, { status: 401 }),
    };
  }

  return { user: data.user };
}
