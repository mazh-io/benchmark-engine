'use client';

import type { ReactElement } from 'react';
import type { ModelData } from './hooks/useHeadToHeadStats';

interface Props {
  model1: ModelData;
  model2: ModelData;
  allModels: ModelData[];
  onViewProviders: () => void;
}

export function HeadToHeadBenchmark({ model1, model2, allModels, onViewProviders }: Props): ReactElement {
  const rank = (key: keyof ModelData, lower: boolean) => {
    const sorted = [...allModels].sort((a, b) =>
      lower ? (a[key] as number) - (b[key] as number) : (b[key] as number) - (a[key] as number),
    );
    return sorted.findIndex((m) => m.id === model1.id || m.id === model2.id) + 1;
  };

  const leader = (v1: number, v2: number, lower: boolean) =>
    lower ? (v1 < v2 ? model1 : model2) : (v1 > v2 ? model1 : model2);

  const marketTTFT = allModels[0];
  const marketTPS = [...allModels].sort((a, b) => b.tps - a.tps)[0];
  const leaderTTFT = leader(model1.ttft, model2.ttft, true);
  const leaderTPS = leader(model1.tps, model2.tps, false);

  const items = [
    {
      label: 'TTFT',
      rank: rank('ttft', true),
      gap: leaderTTFT.ttft > 0 && marketTTFT.ttft > 0
        ? (leaderTTFT.ttft / marketTTFT.ttft).toFixed(1) : null,
    },
    {
      label: 'TPS',
      rank: rank('tps', false),
      gap: leaderTPS.tps > 0 && marketTPS.tps > 0
        ? (marketTPS.tps / leaderTPS.tps).toFixed(1) : null,
    },
    {
      label: 'Success',
      rank: rank('success', false),
      gap: null,
    },
  ];

  return (
    <div className="h2h-benchmark">
      <div className="h2h-benchmark-title">💡 Market Benchmark</div>
      <div className="h2h-benchmark-body">
        <div className="h2h-benchmark-list">
          {items.map((it) => {
            const isLeader = it.rank === 1;
            return (
              <div key={it.label} className="h2h-benchmark-item">
                <span className="h2h-benchmark-metric">{it.label}</span>
                <span className={`h2h-benchmark-rank ${isLeader ? 'leader' : 'gap'}`}>
                  #{it.rank}
                </span>
                <span className={`h2h-benchmark-text ${isLeader ? 'leader' : ''}`}>
                  {isLeader ? 'You picked the leader!' : it.gap ? `${it.gap}× gap to leader` : 'Gap to leader'}
                </span>
              </div>
            );
          })}
        </div>
        <button className="h2h-benchmark-cta" onClick={onViewProviders}>
          See who's leading →
        </button>
      </div>
    </div>
  );
}
