"use client";

import { useEffect, useState } from 'react';
import { api, type RunRecord } from '@/services/api';

export function useRuns() {
  const [data, setData] = useState<RunRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = () => {
    setLoading(true);
    api.runs()
      .then((result) => {
        setData(result);
      })
      .catch(() => {
        setData([]);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    refresh();
  }, []);

  return { data, loading, refresh };
}
