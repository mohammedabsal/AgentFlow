"use client";

import { useEffect, useState } from 'react';
import { createWebSocketUrl } from '@/services/api';

export function useRunStream(runId: string | null) {
  const [events, setEvents] = useState<Array<Record<string, unknown>>>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!runId) {
      setEvents([]);
      setConnected(false);
      return;
    }

    const socket = new WebSocket(createWebSocketUrl(`/api/runs/ws/${runId}`));

    socket.onopen = () => setConnected(true);
    socket.onmessage = (event) => {
      try {
        setEvents((current) => [...current, JSON.parse(event.data as string) as Record<string, unknown>]);
      } catch {
        setEvents((current) => [
          ...current,
          {
            type: 'run.message',
            run_id: runId,
            payload: event.data,
          },
        ]);
      }
    };
    socket.onerror = () => setConnected(false);
    socket.onclose = () => setConnected(false);

    return () => {
      socket.close();
    };
  }, [runId]);

  return { events, connected };
}

export interface StreamEvent {
  type: string;
  run_id?: string;
  timestamp: string;
  data: Record<string, any>;
  trace_id?: string;
}

export interface UseRunStreamOptions {
  onEvent?: (event: StreamEvent) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

export function useRunStreamSSE(
  runId: string | null,
  options: UseRunStreamOptions = {}
) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!runId) return;

    const streamUrl = `/api/platform/runs/${runId}/stream`;
    const eventSource = new EventSource(streamUrl);

    setIsConnected(true);
    setError(null);

    eventSource.onopen = () => {
      console.log(`[SSE] Connected to run stream for ${runId}`);
    };

    eventSource.addEventListener('run_started', (e) => {
      const data = JSON.parse(e.data);
      const event: StreamEvent = {
        type: 'run_started',
        run_id: runId,
        timestamp: new Date().toISOString(),
        data,
      };
      setEvents((prev) => [...prev, event]);
      options.onEvent?.(event);
    });

    eventSource.addEventListener('step_started', (e) => {
      const data = JSON.parse(e.data);
      const event: StreamEvent = {
        type: 'step_started',
        run_id: runId,
        timestamp: new Date().toISOString(),
        data,
      };
      setEvents((prev) => [...prev, event]);
      options.onEvent?.(event);
    });

    eventSource.addEventListener('step_completed', (e) => {
      const data = JSON.parse(e.data);
      const event: StreamEvent = {
        type: 'step_completed',
        run_id: runId,
        timestamp: new Date().toISOString(),
        data,
      };
      setEvents((prev) => [...prev, event]);
      options.onEvent?.(event);
    });

    eventSource.addEventListener('run_completed', (e) => {
      const data = JSON.parse(e.data);
      const event: StreamEvent = {
        type: 'run_completed',
        run_id: runId,
        timestamp: new Date().toISOString(),
        data,
      };
      setEvents((prev) => [...prev, event]);
      options.onEvent?.(event);
      options.onComplete?.();
      setIsConnected(false);
    });

    eventSource.onerror = (e) => {
      console.error('[SSE] Error:', e);
      const streamError = new Error('Stream connection failed');
      setError(streamError);
      options.onError?.(streamError);
      setIsConnected(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [runId, options]);

  return {
    events,
    isConnected,
    error,
  };
}

export function useRunLogs(
  runId: string | null,
  options: UseRunStreamOptions = {}
) {
  const [logs, setLogs] = useState<Array<{ level: string; message: string; timestamp: string }>>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!runId) return;

    const streamUrl = `/api/platform/runs/${runId}/logs/stream`;
    const eventSource = new EventSource(streamUrl);

    setIsConnected(true);
    setError(null);

    eventSource.addEventListener('log_entry', (e) => {
      const data = JSON.parse(e.data);
      setLogs((prev) => [...prev, data]);
      const event: StreamEvent = {
        type: 'log_entry',
        run_id: runId,
        timestamp: data.timestamp,
        data,
      };
      options.onEvent?.(event);
    });

    eventSource.onerror = (e) => {
      console.error('[SSE Logs] Error:', e);
      const streamError = new Error('Logs stream connection failed');
      setError(streamError);
      options.onError?.(streamError);
      setIsConnected(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [runId, options]);

  return {
    logs,
    isConnected,
    error,
  };
}

export function useRunArtifacts(
  runId: string | null,
  options: UseRunStreamOptions = {}
) {
  const [artifacts, setArtifacts] = useState<
    Array<{ kind: string; path: string; size_bytes: number; index: number }>
  >([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [totalArtifacts, setTotalArtifacts] = useState(0);

  useEffect(() => {
    if (!runId) return;

    const streamUrl = `/api/platform/runs/${runId}/artifacts/stream`;
    const eventSource = new EventSource(streamUrl);

    setIsConnected(true);
    setError(null);

    eventSource.addEventListener('artifacts_start', (e) => {
      const data = JSON.parse(e.data);
      setTotalArtifacts(data.total_artifacts);
      const event: StreamEvent = {
        type: 'artifacts_start',
        run_id: runId,
        timestamp: new Date().toISOString(),
        data,
      };
      options.onEvent?.(event);
    });

    eventSource.addEventListener('artifact_generated', (e) => {
      const data = JSON.parse(e.data);
      setArtifacts((prev) => [...prev, data]);
      const event: StreamEvent = {
        type: 'artifact_generated',
        run_id: runId,
        timestamp: new Date().toISOString(),
        data,
      };
      options.onEvent?.(event);
    });

    eventSource.addEventListener('artifacts_complete', (e) => {
      const data = JSON.parse(e.data);
      const event: StreamEvent = {
        type: 'artifacts_complete',
        run_id: runId,
        timestamp: new Date().toISOString(),
        data,
      };
      options.onEvent?.(event);
      options.onComplete?.();
      setIsConnected(false);
    });

    eventSource.onerror = (e) => {
      console.error('[SSE Artifacts] Error:', e);
      const streamError = new Error('Artifacts stream connection failed');
      setError(streamError);
      options.onError?.(streamError);
      setIsConnected(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [runId, options]);

  return {
    artifacts,
    totalArtifacts,
    isConnected,
    error,
  };
}
