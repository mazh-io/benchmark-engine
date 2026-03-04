import { NextRequest, NextResponse } from 'next/server';
import { getAdminClient } from '@/lib/supabase-admin';
import { authenticateRequest } from '@/lib/server-auth';

export const runtime = 'nodejs';

/**
 * DELETE /api/account
 *
 * Permanently deletes the authenticated user's account.
 * 1. Soft-deletes the row in public.users (is_active -> false)
 * 2. Removes the user from Supabase Auth
 */
export async function DELETE(req: NextRequest) {
  const auth = await authenticateRequest(req);
  if (auth.error) return auth.error;

  const admin = getAdminClient();
  const userId = auth.user.id;

  await admin.from('users').update({ is_active: false }).eq('id', userId);

  const { error } = await admin.auth.admin.deleteUser(userId);
  if (error) {
    return NextResponse.json(
      { error: error.message || 'Failed to delete account' },
      { status: 500 },
    );
  }

  return new NextResponse(null, { status: 204 });
}
