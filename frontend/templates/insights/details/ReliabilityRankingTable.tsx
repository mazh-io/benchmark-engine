'use client';

import type { ReactElement } from 'react';

interface ProviderReliability {
  provider: string;
  success: number;
  stall: number;
  errors5xx: number;
  mtbf: string;
}

interface Props {
  providerStats: ProviderReliability[];
}

export function ReliabilityRankingTable({ providerStats }: Props): ReactElement {
  return (
    <table className="ranking-table">
      <thead>
        <tr>
          <th>Provider</th>
          <th>Success</th>
          <th>Stall</th>
          <th>5xx</th>
          <th>MTBF</th>
        </tr>
      </thead>
      <tbody>
        {providerStats.slice(0, 5).map((stat) => {
          const successClass = stat.success >= 99.5 ? 'metric good' : 
                              stat.success >= 98 ? 'metric' : 'metric bad';
          const stallClass = stat.stall < 5 ? 'metric good' : 
                            stat.stall > 20 ? 'metric bad' : 'metric';
          const error5xxClass = stat.errors5xx < 1 ? 'metric good' : 
                               stat.errors5xx > 2 ? 'metric bad' : 'metric';
          const mtbfClass = parseFloat(stat.mtbf) > 8 ? 'metric good' : 
                           parseFloat(stat.mtbf) < 3 ? 'metric bad' : 'metric';

          return (
            <tr key={stat.provider}>
              <td className="provider-cell">
                <span className="provider">{stat.provider}</span>
              </td>
              <td className={successClass}>{stat.success}%</td>
              <td className={stallClass}>{stat.stall}%</td>
              <td className={error5xxClass}>{stat.errors5xx}%</td>
              <td className={mtbfClass}>{stat.mtbf}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

