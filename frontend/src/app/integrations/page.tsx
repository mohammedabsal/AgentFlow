import { AppShell } from '@/components/app-shell';

const integrations = ['GitHub', 'Slack', 'Stripe', 'OpenAI', 'Anthropic', 'Redis', 'PostgreSQL', 'Omnium'];

export default function IntegrationsPage() {
  return (
    <AppShell>
      <div className="mb-6">
        <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Integrations</div>
        <h1 className="mt-3 text-3xl font-semibold">Connect triggers, tools, model providers, and observability sinks.</h1>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {integrations.map((item) => (
          <article key={item} className="rounded-[2rem] border border-white/10 bg-white/5 p-6 text-center text-sm font-medium text-slate-200 backdrop-blur">
            {item}
          </article>
        ))}
      </div>
    </AppShell>
  );
}
