import React, { useMemo } from 'react';
import { AlertCircle, CheckCircle2, Clock, Zap, AlertTriangle, Loader2 } from 'lucide-react';

export interface LogEntry {
  timestamp: string;
  type: 'run_started' | 'run_completed' | 'run_failed' | 'step_started' | 'step_completed' | 'step_failed' | 'agent_executed' | 'log_entry' | string;
  message: string;
  level?: 'info' | 'error' | 'warning' | 'debug';
  payload?: Record<string, any>;
}

interface LiveLogsPanelProps {
  events: Array<Record<string, unknown>>;
  connected: boolean;
  isRunning?: boolean;
}

function getLogIcon(type: string, level?: string) {
  if (type === 'run_completed' || (type === 'step_completed' && level !== 'error')) {
    return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
  }
  if (type === 'run_failed' || type === 'step_failed' || level === 'error') {
    return <AlertCircle className="h-4 w-4 text-red-500" />;
  }
  if (type === 'run_started' || type === 'step_started') {
    return <Zap className="h-4 w-4 text-blue-500" />;
  }
  if (type === 'agent_executed') {
    return <Clock className="h-4 w-4 text-purple-500" />;
  }
  if (level === 'warning') {
    return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
  }
  return <Clock className="h-4 w-4 text-slate-400" />;
}

function formatEventMessage(event: Record<string, unknown>): string {
  const type = String(event.type || 'unknown');
  const payload = (event.payload || event.data) as Record<string, any> || {};

  switch (type) {
    case 'run_started':
      return `🚀 Run started: ${payload.run_id}`;
    case 'run_completed':
      return `✅ Run completed - ${payload.artifact_count || 0} artifacts generated`;
    case 'run_failed':
      return `❌ Run failed: ${payload.error || 'Unknown error'}`;
    case 'agent_started':
      return `▶ Agent started: ${payload.agent || payload.step_id || 'Unknown agent'}`;
    case 'step_started':
      return `▶ Step started: ${payload.step_name || payload.agent || 'Unknown step'}`;
    case 'agent_completed':
      return `✓ Agent completed: ${payload.agent || payload.step_id || 'Unknown agent'} (${payload.artifact_count || 0} files)`;
    case 'file_generated':
      return `Generated file: ${payload.path || 'unknown path'}`;
    case 'tool_call':
      return `Tool ${payload.tool || 'call'}: ${payload.status || 'completed'}`;
    case 'package_created':
      return `ZIP package ready: ${payload.download_url || ''}`;
    case 'step_completed':
      return `✓ Step completed: ${payload.step_name || payload.agent || 'Unknown step'}`;
    case 'step_failed':
      return `✗ Step failed: ${payload.error || 'Unknown error'}`;
    case 'agent_executed':
      return `🤖 Agent executed: ${payload.role || 'Unknown'} - ${payload.tokens_used || 0} tokens`;
    case 'log_entry':
      return `${payload.message || ''}`;
    default:
      return `${type}: ${JSON.stringify(payload).slice(0, 80)}`;
  }
}

export function LiveLogsPanel({ events, connected, isRunning = false }: LiveLogsPanelProps) {
  const logs: LogEntry[] = useMemo(() => {
    return events.map((event) => {
      const type = String(event.type || 'unknown');
      const payload = (event.payload || event.data) as Record<string, any> || {};
      const timestamp = String(event.timestamp || new Date().toISOString());

      return {
        timestamp,
        type: type as LogEntry['type'],
        message: formatEventMessage(event),
        level: payload.level || (type.includes('failed') ? 'error' : 'info'),
        payload,
      };
    });
  }, [events]);

  return (
    <div className="rounded-lg border border-white/10 bg-slate-950 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <span>Live Logs</span>
          {connected && isRunning && <Loader2 className="h-3 w-3 animate-spin text-cyan-400" />}
          {connected && !isRunning && <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />}
          {!connected && <span className="inline-block h-2 w-2 rounded-full bg-slate-500" />}
        </h3>
        <span className="text-xs text-slate-400">
          {logs.length} {logs.length === 1 ? 'event' : 'events'}
        </span>
      </div>

      <div className="max-h-96 space-y-2 overflow-y-auto font-mono text-xs">
        {logs.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-slate-400">
            <p>Waiting for execution to start...</p>
          </div>
        ) : (
          logs.slice(-20).map((log, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 border-l border-slate-700/50 pl-2 py-1 text-slate-300 hover:bg-slate-900/50"
            >
              <div className="mt-1 flex-shrink-0">
                {getLogIcon(log.type, log.level)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className="text-slate-400 text-[10px]">
                    {new Date(log.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: false,
                    })}
                  </span>
                  <span className={`break-words ${log.level === 'error' ? 'text-red-400' : log.level === 'warning' ? 'text-yellow-400' : 'text-slate-300'}`}>
                    {log.message}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {logs.length > 20 && (
        <div className="mt-2 text-center text-xs text-slate-400">
          ... and {logs.length - 20} earlier events
        </div>
      )}
    </div>
  );
}
