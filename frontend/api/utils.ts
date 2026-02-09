/**
 * Utility Functions
 *
 * Shared helpers used across the frontend application.
 */

// ============================================================================
// MODEL NAME RESOLUTION
// ============================================================================

/**
 * Resolve display-friendly model name for a provider
 *
 * Handles shortening of verbose model paths:
 * - Together: "meta-llama/Meta-Llama-3.1-405B" → "meta-llama"
 * - Fireworks: "accounts/fireworks/models/llama-v3p3-70b" → "llama-v3p3-70b"
 *
 * @param providerKey - Provider identifier (e.g. "groq", "together")
 * @param results - Benchmark results to search through
 * @returns Shortened model name or undefined
 */
export function resolveModelName(
  providerKey: string,
  results?: {
    provider?: string | null;
    providers?: { name?: string } | null;
    model?: string | null;
    models?: { name?: string } | null;
  }[],
): string | undefined {
  if (!results) return;

  const key = providerKey.toLowerCase();

  const match = results.find(
    (r) =>
      r.provider?.toLowerCase() === key ||
      r.providers?.name?.toLowerCase() === key,
  );

  const modelName = match?.model || match?.models?.name;
  if (!modelName) return;

  // Together: "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo" → "meta-llama"
  if (key === 'together' && modelName.includes('/')) {
    return modelName.split('/')[0];
  }

  // Fireworks: "accounts/fireworks/models/llama-v3p3-70b-instruct" → "llama-v3p3-70b-instruct"
  if (key === 'fireworks' && modelName.includes('/')) {
    const parts = modelName.split('/');
    return parts[parts.length - 1];
  }

  return modelName;
}
