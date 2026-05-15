"use client";

import { useEffect, useState } from 'react';
import { api } from '@/services/api';

export function useHealth() {
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    api.health()
      .then(() => {
        if (active) setHealthy(true);
      })
      .catch(() => {
        if (active) setHealthy(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return { healthy };
}
