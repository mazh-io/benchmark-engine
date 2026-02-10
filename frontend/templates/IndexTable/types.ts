import type { ProviderMetrics } from '@/api/types';

export type RowData = {
  rank: number;
  providerKey: string;
  providerDisplay: string;
  modelName: string;
  type: 'OPEN' | 'PROP';
  ttftMs: number | null;
  tps: number | null;
  ttftDelta24h?: number | null;
  tpsDelta24h?: number | null;
  jitterMs: number;
  jitterColor: ProviderMetrics['jitterColor'];
  pricePerM: number;
  valueScore: number;
};
