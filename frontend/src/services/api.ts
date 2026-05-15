const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api';
const apiOrigin = new URL(baseUrl).origin;

export interface ProjectRecord {
  id: string;
  workspace_id: string;
  name: string;
  prompt: string;
  description?: string | null;
  status: string;
  project_metadata: Record<string, unknown>;
}

export interface RunRecord {
  id: string;
  project_id: string;
  plan_id: string;
  status: string;
  prompt_input: Record<string, unknown>;
  output: Record<string, unknown>;
  state: Record<string, unknown>;
  error?: string | null;
  trace_id?: string | null;
}

export interface ArtifactRecord {
  id: string;
  run_id: string;
  kind: string;
  path: string;
  content: string;
  artifact_metadata: Record<string, unknown>;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function createWebSocketUrl(path: string): string {
  const url = new URL(apiOrigin);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = path.startsWith('/') ? path : `/${path}`;
  url.search = '';
  return url.toString();
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  workflows: () => request<Array<Record<string, unknown>>>('/workflows'),
  workflow: (workflowId: string) => request<Record<string, unknown>>(`/workflows/${workflowId}`),
  executions: () => request<Array<Record<string, unknown>>>('/executions'),
  execution: (executionId: string) => request<Record<string, unknown>>(`/executions/${executionId}`),
  projects: () => request<ProjectRecord[]>('/projects'),
  project: (projectId: string) => request<ProjectRecord>(`/projects/${projectId}`),
  createProject: (payload: { workspace_id?: string; workspace_name?: string; name: string; prompt: string; description?: string }) =>
    request<ProjectRecord>('/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  projectPlans: (projectId: string) => request<Array<Record<string, unknown>>>(`/projects/${projectId}/plans`),
  createPlan: (projectId: string, payload?: { objective?: string; hints?: Record<string, unknown> }) =>
    request<Record<string, unknown>>(`/projects/${projectId}/plans`, {
      method: 'POST',
      body: JSON.stringify(payload ?? {}),
    }),
  createRun: (projectId: string, payload?: { prompt_override?: string; context?: Record<string, unknown> }) =>
    request<RunRecord>(`/projects/${projectId}/runs`, {
      method: 'POST',
      body: JSON.stringify(payload ?? {}),
    }),
  runs: () => request<RunRecord[]>('/runs'),
  run: (runId: string) => request<RunRecord>(`/runs/${runId}`),
  retryRun: (runId: string) => request<RunRecord>(`/runs/${runId}/retry`, { method: 'POST' }),
  artifacts: (runId: string) => request<ArtifactRecord[]>(`/runs/${runId}/artifacts`),
};
