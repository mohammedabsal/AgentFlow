"use client";

import { useEffect, useState } from 'react';
import { api } from '@/services/api';

export function useExecutions() {
  const [data, setData] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    api.executions()
      .then((result) => {
        if (active) setData(result);
      })
      .catch(() => {
        if (active) setData([]);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return { data, loading };
}
