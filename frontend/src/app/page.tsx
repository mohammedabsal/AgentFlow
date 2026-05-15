"use client";

import { ArrowRight, Bot, Cpu, GitBranch, MessageSquareText, Radar, Sparkles, ShieldCheck } from 'lucide-react';
import Link from 'next/link';
import { AppShell } from '@/components/app-shell';
import { StatCard } from '@/components/stat-card';
import { WorkflowCanvas } from '@/components/workflow-canvas';
import { LiveLogsPanel } from '@/components/live-logs-panel';
import { ArtifactList } from '@/components/code-viewer';
import { useProjects } from '@/hooks/use-projects';
import { useRuns } from '@/hooks/use-runs';
import { useHealth } from '@/hooks/use-health';
import { useRunStream } from '@/hooks/use-run-stream';
import { api, type ArtifactRecord, type ProjectRecord, type RunRecord } from '@/services/api';
import { useState } from 'react';

export const dynamic = 'force-dynamic';

const highlights = [
  {
    icon: GitBranch,
    title: 'Planner-worker orchestration',
    body: 'Break a single prompt into structured tasks, delegate them to specialized agents, and keep the full causal chain observable.',
  },
  {
    icon: Radar,
    title: 'Deep observability',
    body: 'Track logs, retries, tool calls, and execution transitions in real time with replayable history.',
  },
  {
    icon: ShieldCheck,
    title: 'Safe execution primitives',
    body: 'Sandbox tools, bound retries, enforce timeouts, and persist every state change for recovery.',
  },
];

const samplePrompts = [
  'Build a subscription SaaS dashboard with auth, billing, and team workspaces.',
  'Create a project tracker with realtime collaboration and AI-generated status summaries.',
  'Ship a design-to-code platform that converts product prompts into deployable web apps.',
];

export default function DashboardPage() {
  const { healthy } = useHealth();
  const { data: projects, loading: projectsLoading, refresh: refreshProjects } = useProjects();
  const { data: runs, loading: runsLoading, refresh: refreshRuns } = useRuns();
  const [prompt, setPrompt] = useState(samplePrompts[0]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Ready to generate a project.');
  const [generatedProject, setGeneratedProject] = useState<ProjectRecord | null>(null);
  const [generatedRun, setGeneratedRun] = useState<RunRecord | null>(null);
  const [generatedArtifacts, setGeneratedArtifacts] = useState<ArtifactRecord[]>([]);
  const activeRunId = generatedRun?.id ?? runs[0]?.id ?? null;
  const { events: runEvents, connected: runConnected } = useRunStream(activeRunId);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setStatusMessage('Planning architecture, agents, and project structure...');
    try {
      const name = prompt.split(/[.!?]/)[0].slice(0, 48) || 'New autonomous app';
      const project = await api.createProject({
        name,
        prompt,
        workspace_name: 'Studio Workspace',
      });
      const run = await api.createRun(project.id, { context: { source: 'studio_prompt' } });
      let artifacts: ArtifactRecord[] = [];
      try {
        artifacts = await api.artifacts(run.id);
      } catch {
        artifacts = [];
      }
      setGeneratedProject(project);
      setGeneratedRun(run);
      setGeneratedArtifacts(artifacts);
      refreshProjects();
      refreshRuns();
      setStatusMessage(`Project generated and run ${run.status}.`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Generation failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  const visibleProject = generatedProject ?? projects[0] ?? null;
  const visibleRun = generatedRun ?? runs[0] ?? null;
  const visibleArtifacts = generatedArtifacts.length > 0 ? generatedArtifacts : visibleRun ? [] : [];

  return (
    <AppShell>
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6 rounded-[2.25rem] border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.16),transparent_30%),linear-gradient(135deg,rgba(15,23,42,0.96),rgba(2,6,23,0.9))] p-8 shadow-glow">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-cyan-200">
            <Sparkles className="h-3 w-3" />
            AgentFlow Studio
          </div>
          <h1 className="max-w-3xl text-4xl font-semibold leading-tight md:text-6xl">
            One prompt becomes a product plan, a workspace, and a deployable app.
          </h1>
          <p className="max-w-2xl text-base leading-7 text-slate-300 md:text-lg">
            The studio plans architecture, generates frontend and backend code, retries failures,
            runs tests, and prepares deployment-ready artifacts with a Lovable-inspired UX.
          </p>

          <div className="grid gap-4 md:grid-cols-3">
            <StatCard label="Backend status" value={healthy === null ? 'Checking' : healthy ? 'Online' : 'Offline'} detail="FastAPI health endpoint connection check." />
            <StatCard label="Projects" value={String(projects.length)} detail="Prompt-driven workspaces stored in the platform." />
            <StatCard label="Runs" value={String(runs.length)} detail="Planning and execution history for each project." />
          </div>

          <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-cyan-300/80">
              <MessageSquareText className="h-4 w-4" />
              Prompt studio
            </div>
            <label className="mt-4 block text-sm text-slate-300">Describe the app you want to generate.</label>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              className="mt-3 min-h-44 w-full rounded-[1.75rem] border border-white/10 bg-slate-950/70 p-5 text-sm leading-7 text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/50"
              placeholder="Example: Build a collaborative AI app builder with auth, previews, deployment, and agent logs."
            />
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleGenerate}
                disabled={isGenerating}
                className="inline-flex items-center gap-2 rounded-2xl bg-cyan-300 px-5 py-3 font-medium text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isGenerating ? 'Generating...' : 'Generate app'}
                <ArrowRight className="h-4 w-4" />
              </button>
              {samplePrompts.map((sample) => (
                <button
                  key={sample}
                  type="button"
                  onClick={() => setPrompt(sample)}
                  className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200 transition hover:bg-white/10"
                >
                  Use sample
                </button>
              ))}
            </div>
            <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-slate-300">{statusMessage}</div>
          </div>

          <div className="rounded-[2rem] border border-cyan-300/20 bg-[linear-gradient(180deg,rgba(34,211,238,0.14),rgba(15,23,42,0.9))] p-6 shadow-glow backdrop-blur">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Generated app</div>
                <h2 className="mt-2 text-2xl font-semibold">The newest result is always visible here.</h2>
              </div>
              <div className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-cyan-100">
                Live
              </div>
            </div>

            {visibleProject ? (
              <div className="mt-5 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
                <article className="rounded-[1.75rem] border border-white/10 bg-slate-950/60 p-5">
                  <div className="text-xs uppercase tracking-[0.3em] text-slate-500">Project</div>
                  <div className="mt-3 text-2xl font-semibold text-white">{visibleProject.name}</div>
                  <p className="mt-3 text-sm leading-7 text-slate-300">{visibleProject.prompt}</p>
                  <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-400">
                    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">{visibleProject.status}</span>
                    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Workspace {visibleProject.workspace_id.slice(0, 8)}</span>
                    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Project {visibleProject.id.slice(0, 8)}</span>
                  </div>
                </article>

                <article className="rounded-[1.75rem] border border-white/10 bg-slate-950/60 p-5">
                  <div className="text-xs uppercase tracking-[0.3em] text-slate-500">Run</div>
                  {visibleRun ? (
                    <>
                      <div className="mt-3 flex items-center justify-between gap-4">
                        <div className="text-2xl font-semibold text-white">{visibleRun.status}</div>
                        <div className="text-xs uppercase tracking-[0.2em] text-slate-500">{visibleRun.id.slice(0, 8)}</div>
                      </div>
                      <div className="mt-4 grid gap-3 md:grid-cols-2">
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                          <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Plan</div>
                          <div className="mt-2 font-medium text-white">{visibleRun.plan_id.slice(0, 8)}</div>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                          <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Project</div>
                          <div className="mt-2 font-medium text-white">{visibleRun.project_id.slice(0, 8)}</div>
                        </div>
                      </div>
                      <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm leading-7 text-slate-300">
                        {typeof visibleRun.output?.summary === 'string' && visibleRun.output.summary.length > 0
                          ? visibleRun.output.summary
                          : 'The run is executing and the backend is streaming result state into the platform.'}
                      </div>
                    </>
                  ) : (
                    <div className="mt-4 text-sm text-slate-400">Create a project to surface the latest run here.</div>
                  )}
                </article>
              </div>
            ) : (
              <div className="mt-5 rounded-[1.75rem] border border-white/10 bg-slate-950/60 p-5 text-sm text-slate-400">
                No generated project yet. Use the prompt box above to create the first one.
              </div>
            )}

            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4 text-sm text-slate-300">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Artifacts</div>
                <div className="mt-2 font-medium text-white">{visibleArtifacts.length}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4 text-sm text-slate-300">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Projects</div>
                <div className="mt-2 font-medium text-white">{projects.length}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4 text-sm text-slate-300">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Runs</div>
                <div className="mt-2 font-medium text-white">{runs.length}</div>
              </div>
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
            <LiveLogsPanel 
              events={runEvents} 
              connected={runConnected}
              isRunning={visibleRun?.status === 'running'}
            />
          </div>

          {visibleArtifacts.length > 0 && (
            <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
              <div className="mb-4 text-xs uppercase tracking-[0.3em] text-cyan-300/80">
                Generated artifacts
              </div>
              <ArtifactList artifacts={visibleArtifacts} />
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            <article className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-cyan-300/80">
                <Bot className="h-4 w-4" />
                AI activity timeline
              </div>
              <div className="mt-4 space-y-3 text-sm text-slate-300">
                {[
                  'Planner Agent expanded the prompt into a roadmap.',
                  'Architect Agent defined schema, APIs, and state flow.',
                  'Frontend and Backend Agents are ready to generate scaffolds.',
                  'Testing Agent will validate the generated workspace.',
                ].map((line) => (
                  <div key={line} className="rounded-2xl border border-white/10 bg-slate-950/50 px-4 py-3">
                    {line}
                  </div>
                ))}
              </div>
            </article>

            <article className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-cyan-300/80">
                <Cpu className="h-4 w-4" />
                Recent projects
              </div>
              <div className="mt-4 space-y-3 text-sm text-slate-300">
                {projectsLoading ? (
                  <div className="text-slate-400">Loading projects...</div>
                ) : projects.length === 0 ? (
                  <div className="text-slate-400">No projects created yet. Generate the first one above.</div>
                ) : (
                  projects.slice(0, 4).map((project) => (
                    <div key={project.id} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                      <div className="font-medium text-white">{project.name}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">{project.status}</div>
                      <div className="mt-2 text-xs leading-6 text-slate-400">{project.prompt}</div>
                    </div>
                  ))
                )}
              </div>
            </article>
          </div>
        </div>

        <div className="grid gap-4">
          <WorkflowCanvas />

          <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
            <div className="flex items-center justify-between">
              <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Latest runs</div>
              <Link href="/runs" className="text-xs uppercase tracking-[0.2em] text-slate-400 transition hover:text-white">
                Open run queue
              </Link>
            </div>
            <div className="mt-4 space-y-3">
              {runsLoading ? (
                <div className="text-sm text-slate-400">Loading runs...</div>
              ) : runs.length === 0 ? (
                <div className="text-sm text-slate-400">No runs yet. Create a project to start one.</div>
              ) : (
                runs.slice(0, 4).map((run) => (
                  <div key={run.id} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4 text-sm text-slate-300">
                    <div className="flex items-center justify-between gap-4">
                      <div className="font-medium text-white">{run.status}</div>
                      <div className="text-xs uppercase tracking-[0.2em] text-slate-500">{run.plan_id.slice(0, 8)}</div>
                    </div>
                    <div className="mt-2 text-xs text-slate-500">Run {run.id.slice(0, 8)} · Project {run.project_id.slice(0, 8)}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(15,23,42,0.9),rgba(2,6,23,0.96))] p-6 backdrop-blur">
            <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Live logs</div>
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              {(runEvents.length > 0
                ? runEvents.slice(-6).map((event, index) => `[${String(event.type)}] ${JSON.stringify(event.payload ?? event.data ?? {}, null, 0)}`)
                : [
                    '[planner] roadmap generated',
                    '[architect] schema and API contracts drafted',
                    '[frontend] workspace shell and streaming UI scaffolded',
                    '[backend] orchestration service wired',
                    visibleRun ? `[run] ${visibleRun.status} · ${visibleRun.id.slice(0, 8)}` : '[run] waiting for first generation',
                  ]
              ).map((line, idx) => (
                <div key={`${String(line)}-${idx}`} className="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 font-mono text-xs text-slate-400">
                  {line}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-3">
        {highlights.map((item) => {
          const Icon = item.icon;
          return (
            <article key={item.title} className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
              <Icon className="h-5 w-5 text-cyan-300" />
              <h2 className="mt-4 text-xl font-semibold">{item.title}</h2>
              <p className="mt-3 text-sm leading-7 text-slate-400">{item.body}</p>
            </article>
          );
        })}
      </section>
    </AppShell>
  );
}
