'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Code,
  Loader,
  CheckCircle,
  AlertCircle,
  Play,
  Pause,
  Download,
  Share2,
} from 'lucide-react';
import { LivePreview } from '@/components/live-preview';
import { WorkspaceSidebar } from '@/components/workspace-sidebar';
import { AgentStatusDashboard } from '@/components/agent-status-dashboard';
import { LogsViewer } from '@/components/logs-viewer';
import { api, createWebSocketUrl, type ArtifactRecord } from '@/services/api';

export default function BuilderPage() {
  const [projectName, setProjectName] = useState('');
  const [userPrompt, setUserPrompt] = useState('');
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
  const [logs, setLogs] = useState<Array<{ type: string; message: string; timestamp: string }>>([]);
  const [artifacts, setArtifacts] = useState<Array<{ id: string; path: string; content: string; language: string }>>([]);
  const [liveFiles, setLiveFiles] = useState<Array<{ id: string; path: string; content: string; language: string }>>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedPanel, setExpandedPanel] = useState<'code' | 'preview' | 'logs'>('code');
  const websocketRef = useRef<WebSocket | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Start workflow execution
  const handleStartWorkflow = async () => {
    if (!projectName.trim() || !userPrompt.trim()) {
      alert('Please enter project name and description');
      return;
    }

    setLoading(true);
    setStatus('running');
    setLogs([]);
    setArtifacts([]);
    setLiveFiles([]);

    try {
      const project = await api.createProject({
        name: projectName,
        prompt: userPrompt,
        workspace_name: 'Builder Workspace',
      });
      const run = await api.createRun(project.id, { context: { source: 'builder_page' } });

      setRunId(run.id);
      addLog('info', `Queued run ${run.id}`);

      connectWebSocket(run.id);
      refreshArtifacts(run.id);
      startPolling(run.id);
    } catch (error) {
      console.error('Failed to start workflow:', error);
      setStatus('error');
      setLoading(false);
      addLog('error', `Failed to start workflow: ${error}`);
    }
  };

  // Connect to WebSocket for streaming updates
  const connectWebSocket = (activeRunId: string) => {
    const ws = new WebSocket(createWebSocketUrl(`/api/runs/ws/${activeRunId}`));

    ws.onopen = () => {
      addLog('info', 'Connected to run event stream');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleStreamMessage(message, activeRunId);
      } catch (error) {
        console.error('Failed to parse message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      addLog('error', 'Connection error');
    };

    ws.onclose = () => {
      addLog('info', 'Stream connection closed');
      setLoading(false);
    };

    websocketRef.current = ws;
  };

  // Handle incoming stream messages
  const handleStreamMessage = (message: any, activeRunId: string) => {
    const data = message.data || message.payload || {};
    switch (message.type) {
      case 'connected':
        addLog('info', `Connected to run ${activeRunId}`);
        break;
      case 'run_started':
        addLog('info', 'Run started');
        break;
      case 'agent_started':
        addLog('info', `Agent started: ${data.agent || data.step_id || 'unknown'}`);
        break;
      case 'agent_completed':
        addLog('info', `Agent completed: ${data.agent || data.step_id || 'unknown'}`);
        refreshArtifacts(activeRunId);
        break;
      case 'file_generated': {
        const path = String(data.path || 'generated/file.txt');
        addLog('info', `Generated: ${path}`);
        addLiveFile(path, String(data.source || data.agent || 'agent'));
        refreshArtifacts(activeRunId);
        break;
      }
      case 'tool_call':
        addLog('info', `Tool ${data.tool || 'call'} ${data.status || ''}`);
        break;
      case 'package_created':
        addLog('info', `Package ready: ${data.download_url || ''}`);
        refreshArtifacts(activeRunId);
        break;
      case 'run_completed':
        setStatus('completed');
        addLog('info', 'Run completed');
        refreshArtifacts(activeRunId);
        setTimeout(() => refreshArtifacts(activeRunId), 1200);
        setLoading(false);
        break;
      case 'run_failed':
      case 'agent_failed':
        setStatus('error');
        addLog('error', String(data.error || 'Run failed'));
        setLoading(false);
        break;
      default:
        if (message.content) addLog('info', String(message.content));
        break;
    }
  };

  const startPolling = (activeRunId: string) => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
    }

    pollRef.current = setInterval(async () => {
      try {
        const run = await api.run(activeRunId);
        await refreshArtifacts(activeRunId);

        if (run.status === 'completed') {
          setStatus('completed');
          setLoading(false);
          if (pollRef.current) clearInterval(pollRef.current);
        }

        if (run.status === 'failed') {
          setStatus('error');
          setLoading(false);
          addLog('error', run.error || 'Run failed');
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch (error) {
        addLog('error', `Polling failed: ${error instanceof Error ? error.message : String(error)}`);
      }
    }, 2500);
  };

  const refreshArtifacts = async (activeRunId: string) => {
    try {
      const records = await api.artifacts(activeRunId);
      setArtifacts(records.map(toBuilderArtifact));
      if (!selectedArtifact && records[0]) {
        setSelectedArtifact(records[0].id);
      }
    } catch (error) {
      addLog('error', `Failed to load artifacts: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const toBuilderArtifact = (artifact: ArtifactRecord) => ({
    id: artifact.id,
    path: artifact.path,
    content: artifact.content,
    language: getLanguage(artifact.path),
  });

  const getLanguage = (path: string) => {
    if (path.endsWith('.py')) return 'python';
    if (path.endsWith('.ts') || path.endsWith('.tsx')) return 'typescript';
    if (path.endsWith('.json')) return 'json';
    if (path.endsWith('.sql')) return 'sql';
    if (path.endsWith('.md')) return 'markdown';
    if (path.endsWith('.yml') || path.endsWith('.yaml')) return 'yaml';
    return 'javascript';
  };

  const addLiveFile = (path: string, source: string) => {
    const id = `live-${path}`;
    setLiveFiles((current) => {
      if (current.some((file) => file.path === path)) return current;
      return [
        ...current,
        {
          id,
          path,
          language: getLanguage(path),
          content: `// ${path} generated by ${source}. Full content is persisted when the run completes.`,
        },
      ];
    });
    if (!selectedArtifact) {
      setSelectedArtifact(id);
    }
  };

  const visibleArtifacts = artifacts.length > 0
    ? artifacts
    : liveFiles;

  const addLog = (type: string, message: string) => {
    setLogs((prev) => [
      ...prev,
      {
        type,
        message,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);
  };

  // Cancel execution
  const handleCancel = async () => {
    if (!runId) return;

    try {
      setStatus('idle');
      setLoading(false);
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    } catch (error) {
      console.error('Failed to cancel:', error);
    }
  };

  return (
    <div className="flex h-screen bg-slate-900">
      {/* Left Sidebar - Workspace */}
      <WorkspaceSidebar
        projectName={projectName}
        artifacts={visibleArtifacts}
        selectedArtifact={selectedArtifact}
        onSelectArtifact={setSelectedArtifact}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="bg-slate-800 border-b border-slate-700 p-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Code className="w-6 h-6 text-blue-400" />
            <div>
              <h1 className="text-lg font-semibold text-white">{projectName || 'New Project'}</h1>
              <p className="text-sm text-slate-400">Autonomous AI Software Engineering</p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExpandedPanel(expandedPanel === 'preview' ? 'code' : 'preview')}
            >
              {expandedPanel === 'preview' ? 'View Code' : 'Preview'}
            </Button>
            {status === 'running' && (
              <Button variant="destructive" size="sm" onClick={handleCancel}>
                <Pause className="w-4 h-4 mr-2" />
                Cancel
              </Button>
            )}
            {status === 'completed' && runId && (
              <Button variant="default" size="sm" onClick={() => { window.location.href = api.downloadUrl(runId); }}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-hidden flex">
          {/* Chat/Input Panel */}
          <div className="w-96 bg-slate-800 border-r border-slate-700 flex flex-col p-6">
            <div className="flex-1 overflow-y-auto space-y-4 mb-6">
              {status === 'idle' ? (
                <div className="text-center py-8">
                  <Code className="w-12 h-12 text-slate-600 mx-auto mb-2" />
                  <p className="text-slate-400">Describe your project to get started</p>
                </div>
              ) : (
                <AgentStatusDashboard logs={logs} />
              )}
            </div>

            {/* Input Form */}
            <div className="space-y-4">
              <Input
                placeholder="Project name"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white"
                disabled={loading}
              />

              <Textarea
                placeholder="Describe what you want to build... (e.g., 'Build a todo app with React, Node.js backend, PostgreSQL database')"
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white min-h-32 resize-none"
                disabled={loading}
              />

              <Button
                onClick={handleStartWorkflow}
                disabled={loading || status !== 'idle'}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {loading ? (
                  <>
                    <Loader className="w-4 h-4 mr-2 animate-spin" />
                    Building...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Generate Project
                  </>
                )}
              </Button>

              {/* Status Indicator */}
              <div className="flex items-center gap-2 text-sm">
                {status === 'running' && (
                  <>
                    <Loader className="w-4 h-4 text-blue-400 animate-spin" />
                    <span className="text-blue-400">Generating...</span>
                  </>
                )}
                {status === 'completed' && (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span className="text-green-400">Completed</span>
                  </>
                )}
                {status === 'error' && (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-400" />
                    <span className="text-red-400">Error</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Code/Preview Panel */}
          <div className="flex-1 flex flex-col">
            {expandedPanel === 'preview' ? (
              <LivePreview artifacts={visibleArtifacts} selectedId={selectedArtifact} />
            ) : (
              <div className="flex-1 bg-slate-900 flex flex-col">
                {selectedArtifact && visibleArtifacts.find((a) => a.id === selectedArtifact) ? (
                  <>
                    <div className="bg-slate-800 border-b border-slate-700 p-3 flex justify-between items-center">
                      <code className="text-sm text-slate-400">
                        {visibleArtifacts.find((a) => a.id === selectedArtifact)?.path}
                      </code>
                      <Button variant="ghost" size="sm">
                        <Share2 className="w-4 h-4" />
                      </Button>
                    </div>
                    <pre className="flex-1 overflow-auto p-4 text-sm text-slate-300 font-mono">
                      {visibleArtifacts.find((a) => a.id === selectedArtifact)?.content}
                    </pre>
                  </>
                ) : (
                  <div className="flex-1 flex items-center justify-center text-slate-400">
                    <p>No artifacts generated yet</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Logs Panel - Bottom */}
        {logs.length > 0 && (
          <div className="bg-slate-800 border-t border-slate-700 h-48">
            <LogsViewer logs={logs} />
          </div>
        )}
      </div>
    </div>
  );
}
