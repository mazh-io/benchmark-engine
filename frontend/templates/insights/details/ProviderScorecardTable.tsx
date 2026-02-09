'use client';

import type { ReactElement } from 'react';

interface ProviderScorecardData {
  provider: string;
  modelCount: number;
  avgTTFT: number;
  avgTPS: number;
  priceRange: string;
  bestFor: string;
}

interface Props {
  providerScores: ProviderScorecardData[];
}

export function ProviderScorecardTable({ providerScores }: Props): ReactElement {
  return (
    <table className="ranking-table">
      <thead>
        <tr>
          <th>Provider</th>
          <th>Models</th>
          <th>TTFT</th>
          <th>TPS</th>
          <th>Price</th>
          <th>Best For</th>
        </tr>
      </thead>
      <tbody>
        {providerScores.map((score) => {
          // Color coding for TTFT (lower is better)
          const ttftClass = score.avgTTFT === 0 ? 'metric' :
                           score.avgTTFT < 300 ? 'metric highlight' :
                           score.avgTTFT < 500 ? 'metric' :
                           score.avgTTFT > 2000 ? 'metric bad' : 'metric';

          // Color coding for TPS (higher is better)
          const tpsClass = score.avgTPS === 0 ? 'metric' :
                          score.avgTPS > 1000 ? 'metric highlight' :
                          score.avgTPS > 400 ? 'metric good' :
                          score.avgTPS < 100 ? 'metric' : 'metric';

          return (
            <tr key={score.provider}>
              <td className="provider-cell">
                <span className="provider">{score.provider}</span>
              </td>
              <td>{score.modelCount}</td>
              <td className={ttftClass}>
                {score.avgTTFT > 0 ? `${score.avgTTFT}ms` : '—'}
              </td>
              <td className={tpsClass}>
                {score.avgTPS > 0 ? score.avgTPS.toLocaleString() : '—'}
              </td>
              <td>{score.priceRange}</td>
              <td>{score.bestFor}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

