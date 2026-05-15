"use client";

import { useEffect, useState } from 'react';
import { api, type ProjectRecord } from '@/services/api';

export function useProjects() {
  const [data, setData] = useState<ProjectRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = () => {
    setLoading(true);
    api.projects()
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
