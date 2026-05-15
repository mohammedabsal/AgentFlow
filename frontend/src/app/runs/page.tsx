"use client";

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/app-shell';
import { useRuns } from '@/hooks/use-runs';
import { api, type ArtifactRecord } from '@/services/api';
import { useRunStream } from '@/hooks/use-run-stream';
import { LiveLogsPanel } from '@/components/live-logs-panel';
import { ArtifactList } from '@/components/code-viewer';

export const dynamic = 'force-dynamic';

export default function RunsPage() {
  const { data: runs, loading } = useRuns();
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactRecord[]>([]);
  const { events, connected } = useRunStream(selectedRunId);

  useEffect(() => {
    if (!selectedRunId && runs.length > 0) {
      setSelectedRunId(runs[0].id);
    }
  }, [runs, selectedRunId]);

  useEffect(() => {
    if (!selectedRunId) {
      setArtifacts([]);
      return;
    }

    let active = true;
    api.artifacts(selectedRunId)
      .then((result) => {
        if (active) {
          setArtifacts(result);
        }
      })
      .catch(() => {
        if (active) {
          setArtifacts([]);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedRunId]);

  return (
    <AppShell>
      <div className="mb-6">
        <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Run Monitor</div>
        <h1 className="mt-3 text-3xl font-semibold">Inspect autonomous runs, outputs, and generated artifacts.</h1>
      </div>
      <div className="grid gap-4 xl:grid-cols-[0.7fr_1.3fr]">
        <div className="space-y-4 rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
          <div className="text-sm font-medium text-slate-300">Runs</div>
          {loading ? (
            <div className="text-sm text-slate-400">Loading runs...</div>
          ) : runs.length === 0 ? (
            <div className="text-sm text-slate-400">No runs yet. Generate a project from the Studio page.</div>
          ) : (
            runs.map((run) => (
              <button
                key={run.id}
                type="button"
                onClick={() => setSelectedRunId(run.id)}
                className={`w-full rounded-[2rem] border p-5 text-left transition ${selectedRunId === run.id ? 'border-cyan-300/40 bg-cyan-400/10' : 'border-white/10 bg-slate-950/50 hover:bg-white/10'}`}
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="text-sm font-medium text-white">{run.status}</div>
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-500">{run.id.slice(0, 8)}</div>
                </div>
                <div className="mt-2 text-xs text-slate-500">Project {run.project_id.slice(0, 8)} · Plan {run.plan_id.slice(0, 8)}</div>
              </button>
            ))
          )}
        </div>

        <div className="space-y-4">
          <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
            <div className="flex items-center justify-between gap-4">
              <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Selected run</div>
              <div className="text-xs uppercase tracking-[0.2em] text-slate-500">{connected ? 'Connected' : 'Waiting'}</div>
            </div>
            <div className="mt-4 text-2xl font-semibold">{selectedRunId ? selectedRunId : 'Select a run'}</div>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              {selectedRunId && runs.find((run) => run.id === selectedRunId) ? (
                <>
                  <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                    <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Status</div>
                    <div className="mt-2 text-lg font-medium text-white">{runs.find((run) => run.id === selectedRunId)?.status}</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                    <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Project</div>
                    <div className="mt-2 text-lg font-medium text-white">{runs.find((run) => run.id === selectedRunId)?.project_id.slice(0, 8)}</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                    <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Plan</div>
                    <div className="mt-2 text-lg font-medium text-white">{runs.find((run) => run.id === selectedRunId)?.plan_id.slice(0, 8)}</div>
                  </div>
                </>
              ) : (
                <div className="text-sm text-slate-400">Choose a run to inspect its output and generated files.</div>
              )}
            </div>
          </section>

          <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
            <LiveLogsPanel 
              events={events}
              connected={connected}
              isRunning={runs.find((run) => run.id === selectedRunId)?.status === 'running'}
            />
          </section>

          <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
            <div className="mb-4 text-xs uppercase tracking-[0.3em] text-cyan-300/80">Generated artifacts</div>
            <ArtifactList artifacts={artifacts} />
          </section>
        </div>
      </div>
    </AppShell>
  );
}
