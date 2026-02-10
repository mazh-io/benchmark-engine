'use client';

import type { ReactElement } from 'react';
import type { JitterColor } from './helpers';
import { getStatusColor } from './helpers';

const BAR_COUNT = 10;

export function JitterBar({ color }: { color: JitterColor }): ReactElement {
  const { bg } = getStatusColor(color);

  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: BAR_COUNT }, (_, i) => (
        <div key={i} className={`h-2 w-1 rounded-sm ${bg}`} />
      ))}
    </div>
  );
}
