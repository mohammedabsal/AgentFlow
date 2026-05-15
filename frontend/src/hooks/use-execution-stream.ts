"use client";

import { useEffect, useState } from 'react';
import { createWebSocketUrl } from '@/services/api';

export function useExecutionStream(executionId: string | null) {
  const [events, setEvents] = useState<Array<Record<string, unknown>>>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!executionId) {
      setEvents([]);
      setConnected(false);
      return;
    }

    const socket = new WebSocket(createWebSocketUrl(`/api/executions/ws/${executionId}`));

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string) as Record<string, unknown>;
        setEvents((current) => [...current, payload]);
      } catch {
        setEvents((current) => [
          ...current,
          {
            type: 'execution.message',
            execution_id: executionId,
            payload: event.data,
          },
        ]);
      }
    };

    socket.onerror = () => {
      setConnected(false);
    };

    socket.onclose = () => {
      setConnected(false);
    };

    return () => {
      socket.close();
    };
  }, [executionId]);

  return { events, connected };
}
