'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Send,
  Code,
  Loader,
  CheckCircle,
  AlertCircle,
  Play,
  Pause,
  Settings,
  Download,
  Share2,
} from 'lucide-react';
import { ExecutionTimeline } from '@/components/execution-timeline';
import { LivePreview } from '@/components/live-preview';
import { WorkspaceSidebar } from '@/components/workspace-sidebar';
import { AgentStatusDashboard } from '@/components/agent-status-dashboard';
import { LogsViewer } from '@/components/logs-viewer';

export default function BuilderPage() {
  const [projectName, setProjectName] = useState('');
  const [userPrompt, setUserPrompt] = useState('');
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
  const [logs, setLogs] = useState<Array<{ type: string; message: string; timestamp: string }>>([]);
  const [artifacts, setArtifacts] = useState<Array<{ id: string; path: string; content: string; language: string }>>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedPanel, setExpandedPanel] = useState<'code' | 'preview' | 'logs'>('code');
  const websocketRef = useRef<WebSocket | null>(null);

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

    try {
      // Call orchestration API
      const response = await fetch('/api/orchestration/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: projectName,
          user_prompt: userPrompt,
          enable_self_healing: true,
          max_iterations: 3,
        }),
      });

      const data = await response.json();
      const newExecutionId = data.execution_id;
      setExecutionId(newExecutionId);

      // Connect to WebSocket for real-time updates
      connectWebSocket(newExecutionId);
    } catch (error) {
      console.error('Failed to start workflow:', error);
      setStatus('error');
      setLoading(false);
      addLog('error', `Failed to start workflow: ${error}`);
    }
  };

  // Connect to WebSocket for streaming updates
  const connectWebSocket = (execId: string) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/orchestration/ws/${execId}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      addLog('info', 'Connected to execution stream');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleStreamMessage(message);
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
  const handleStreamMessage = (message: any) => {
    switch (message.type) {
      case 'log':
        addLog(message.metadata?.level || 'info', message.content);
        break;
      case 'status':
        addLog('info', `Status: ${message.content}`);
        break;
      case 'artifact':
        addLog('info', `Generated: ${message.metadata?.path || message.content}`);
        if (message.metadata?.content) {
          addArtifact(message.metadata.artifact_id, message.metadata.path, message.metadata.content);
        }
        break;
      case 'progress':
        addLog('info', message.content);
        break;
      case 'complete':
        setStatus('completed');
        addLog('info', message.content);
        setLoading(false);
        break;
      case 'error':
        setStatus('error');
        addLog('error', message.content);
        break;
    }
  };

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

  const addArtifact = (id: string, path: string, content: string) => {
    const language = path.endsWith('.py') ? 'python' : path.endsWith('.ts') ? 'typescript' : 'javascript';
    setArtifacts((prev) => [...prev, { id, path, content, language }]);
    if (!selectedArtifact) {
      setSelectedArtifact(id);
    }
  };

  // Cancel execution
  const handleCancel = async () => {
    if (!executionId) return;

    try {
      await fetch(`/api/orchestration/cancel/${executionId}`, { method: 'POST' });
      setStatus('idle');
      setLoading(false);
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
        artifacts={artifacts}
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
            {status === 'completed' && (
              <Button variant="default" size="sm">
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
              <LivePreview artifacts={artifacts} selectedId={selectedArtifact} />
            ) : (
              <div className="flex-1 bg-slate-900 flex flex-col">
                {selectedArtifact && artifacts.find((a) => a.id === selectedArtifact) ? (
                  <>
                    <div className="bg-slate-800 border-b border-slate-700 p-3 flex justify-between items-center">
                      <code className="text-sm text-slate-400">
                        {artifacts.find((a) => a.id === selectedArtifact)?.path}
                      </code>
                      <Button variant="ghost" size="sm">
                        <Share2 className="w-4 h-4" />
                      </Button>
                    </div>
                    <pre className="flex-1 overflow-auto p-4 text-sm text-slate-300 font-mono">
                      {artifacts.find((a) => a.id === selectedArtifact)?.content}
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
