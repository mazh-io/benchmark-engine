/**
 * Single source of truth for deriving first/last name from email (no metadata).
 * - If local part has separators ( . _ - ): use first and last segment (helidona.shabani → Helidona, Shabani).
 * - Otherwise split in half (afrimshabani94 → Afrim, Shabani).
 */
function capitalize(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : '';
}

export function nameFromEmail(email: string): { first: string; last: string } {
  const local = (email.split('@')[0] || 'user').toLowerCase().replace(/\d+$/, '');
  if (local.length <= 2) {
    return { first: capitalize(local) || 'User', last: '' };
  }
  const parts = local.split(/[._-]+/).filter(Boolean);
  if (parts.length >= 2) {
    return {
      first: capitalize(parts[0]),
      last: capitalize(parts[parts.length - 1]),
    };
  }
  const mid = Math.floor(local.length / 2);
  return {
    first: capitalize(local.slice(0, mid)),
    last: capitalize(local.slice(mid)),
  };
}
