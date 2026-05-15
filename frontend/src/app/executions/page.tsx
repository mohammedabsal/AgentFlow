"use client";

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/app-shell';
import { useExecutions } from '@/hooks/use-executions';
import { useExecutionStream } from '@/hooks/use-execution-stream';

export const dynamic = 'force-dynamic';

export default function ExecutionsPage() {
  const { data: executions, loading } = useExecutions();
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const { events, connected } = useExecutionStream(selectedExecutionId);

  useEffect(() => {
    if (!selectedExecutionId && executions.length > 0) {
      setSelectedExecutionId(String(executions[0].id));
    }
  }, [executions, selectedExecutionId]);

  return (
    <AppShell>
      <div className="mb-6">
        <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Execution Monitor</div>
        <h1 className="mt-3 text-3xl font-semibold">Observe live state, retries, logs, and causal traces.</h1>
      </div>
      <div className="grid gap-4 xl:grid-cols-[0.65fr_1.35fr]">
        <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm font-medium text-slate-300">Live feed</div>
            <div className="text-xs uppercase tracking-[0.25em] text-cyan-200/70">{connected ? 'Connected' : 'Disconnected'}</div>
          </div>
          <div className="mt-4 space-y-3 text-sm text-slate-400">
            {events.length === 0 ? (
              <div>{selectedExecutionId ? 'Waiting for execution events...' : 'Create an execution to start streaming events.'}</div>
            ) : (
              events.map((event, index) => (
                <div key={`${String(event.type)}-${index}`} className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                  <div className="text-xs uppercase tracking-[0.2em] text-cyan-200/70">{String(event.type)}</div>
                  <div className="mt-2 text-xs text-slate-400">{JSON.stringify(event.payload ?? {}, null, 0)}</div>
                </div>
              ))
            )}
          </div>
        </div>
        <div className="space-y-4">
          {loading ? (
            <article className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur text-slate-400">Loading executions...</article>
          ) : executions.length === 0 ? (
            <article className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur text-slate-400">No executions yet. Start one from the API or workflow builder.</article>
          ) : (
            executions.map((execution) => (
              <button
                key={String(execution.id)}
                type="button"
                onClick={() => setSelectedExecutionId(String(execution.id))}
                className={`w-full rounded-[2rem] border p-6 text-left backdrop-blur transition ${selectedExecutionId === String(execution.id) ? 'border-cyan-300/40 bg-cyan-400/10' : 'border-white/10 bg-white/5 hover:bg-white/10'}`}
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <div className="text-xs uppercase tracking-[0.3em] text-cyan-200/70">{String(execution.id)}</div>
                    <div className="mt-2 text-lg font-semibold">{String(execution.workflow_id)}</div>
                  </div>
                  <div className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs uppercase tracking-[0.2em] text-slate-300">
                    {String(execution.status)}
                  </div>
                </div>
                <div className="mt-4 text-sm text-slate-400">Trace ID: {execution.trace_id ? String(execution.trace_id) : 'none'}</div>
              </button>
            ))
          )}
        </div>
      </div>
    </AppShell>
  );
}
