"use client";

import { AppShell } from '@/components/app-shell';
import { WorkflowCanvas } from '@/components/workflow-canvas';
import { useWorkflows } from '@/hooks/use-workflows';

export const dynamic = 'force-dynamic';

export default function WorkflowsPage() {
  const { data: workflows, loading } = useWorkflows();

  return (
    <AppShell>
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Workflow Builder</div>
          <h1 className="mt-3 text-3xl font-semibold">Visual DAG orchestration for autonomous systems.</h1>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-400">
            Compose agent, tool, webhook, queue, condition, delay, and memory nodes into durable workflows.
          </p>
        </div>
        <button className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-white transition hover:bg-white/10">
          New workflow
        </button>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.4fr_0.6fr]">
        <WorkflowCanvas />
        <aside className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
          <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Persisted workflows</div>
          <div className="mt-4 space-y-3 text-sm text-slate-300">
            {loading ? (
              <div className="text-slate-400">Loading workflow list...</div>
            ) : workflows.length === 0 ? (
              <div className="text-slate-400">No persisted workflows yet.</div>
            ) : (
              workflows.map((workflow) => (
                <div key={String(workflow.id)} className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                  <div className="font-medium text-white">{String(workflow.name)}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">v{String(workflow.version ?? 1)}</div>
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
