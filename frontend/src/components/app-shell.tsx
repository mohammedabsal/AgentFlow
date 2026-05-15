import Link from 'next/link';
import { Activity, Bot, Boxes, LayoutDashboard, Layers3, Network } from 'lucide-react';

const navItems = [
  { href: '/', label: 'Studio', icon: LayoutDashboard },
  { href: '/workflows', label: 'Workspace Graph', icon: Layers3 },
  { href: '/agents', label: 'Agents', icon: Bot },
  { href: '/runs', label: 'Runs', icon: Activity },
  { href: '/integrations', label: 'Integrations', icon: Boxes },
  { href: '/logs', label: 'Logs', icon: Network },
] as const;

export function AppShell({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="min-h-screen text-white">
      <div className="mx-auto flex min-h-screen max-w-[1600px]">
        <aside className="hidden w-72 border-r border-white/10 bg-white/5 p-6 backdrop-blur xl:flex xl:flex-col">
          <div className="mb-10">
            <div className="text-xs uppercase tracking-[0.4em] text-cyan-300/80">AgentFlow Studio</div>
            <div className="mt-3 text-2xl font-semibold">One prompt to product.</div>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              Chat-driven app generation, self-healing orchestration, live logs, and deploy-ready output.
            </p>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-slate-300 transition hover:bg-white/10 hover:text-white"
                >
                  <Icon className="h-4 w-4 text-cyan-300" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="mt-auto rounded-3xl border border-cyan-400/20 bg-cyan-400/10 p-4 text-sm text-cyan-100 shadow-glow">
            <div className="font-medium">Autonomous loop</div>
            <div className="mt-1 text-cyan-100/80">Plan, generate, test, fix, and deploy with persistent state.</div>
          </div>
        </aside>
        <main className="flex-1 px-4 py-6 md:px-8 lg:px-10">{children}</main>
      </div>
    </div>
  );
}
