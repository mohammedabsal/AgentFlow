import { AppShell } from '@/components/app-shell';

const agents = [
  { name: 'Planner', role: 'Breaks user goals into executable steps.' },
  { name: 'Research', role: 'Searches docs, web, and codebases for context.' },
  { name: 'Coding', role: 'Applies repository changes and generates patches.' },
  { name: 'Reviewer', role: 'Validates output and flags regressions.' },
  { name: 'Execution', role: 'Runs jobs, scripts, and sandboxed code.' },
  { name: 'Notification', role: 'Sends Slack, email, and webhook updates.' },
];

export default function AgentsPage() {
  return (
    <AppShell>
      <div className="mb-6">
        <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Agent Builder</div>
        <h1 className="mt-3 text-3xl font-semibold">Configure prompts, tools, memory, models, and retry policy.</h1>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {agents.map((agent) => (
          <article key={agent.name} className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
            <div className="text-sm uppercase tracking-[0.25em] text-cyan-200/70">{agent.name}</div>
            <p className="mt-4 text-sm leading-7 text-slate-400">{agent.role}</p>
            <div className="mt-6 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-xs text-slate-400">
              Prompt, tools, model provider, memory config, and retry policy are all persisted.
            </div>
          </article>
        ))}
      </div>
    </AppShell>
  );
}
