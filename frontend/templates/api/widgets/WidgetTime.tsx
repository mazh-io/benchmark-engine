'use client';

import { useState, useEffect } from 'react';

export function WidgetTime() {
  const [time, setTime] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      const hh = now.getUTCHours().toString().padStart(2, '0');
      const mm = now.getUTCMinutes().toString().padStart(2, '0');
      setTime(`${hh}:${mm} UTC`);
    };

    update();
    const id = setInterval(update, 60_000);
    return () => clearInterval(id);
  }, []);

  return <span className="w-footer-time">Updated {time}</span>;
}
