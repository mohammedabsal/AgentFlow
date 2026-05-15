import React, { useState } from 'react';
import { Copy, Check, FileCode, ChevronDown } from 'lucide-react';

export interface ArtifactRecord {
  id: string;
  run_id: string;
  kind: string;
  path: string;
  content: string;
  artifact_metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

interface CodeViewerProps {
  artifact: ArtifactRecord;
  isSelected?: boolean;
  onSelect?: () => void;
}

const getLanguageFromPath = (path: string): string => {
  if (path.endsWith('.ts') || path.endsWith('.tsx')) return 'typescript';
  if (path.endsWith('.js') || path.endsWith('.jsx')) return 'javascript';
  if (path.endsWith('.py')) return 'python';
  if (path.endsWith('.json')) return 'json';
  if (path.endsWith('.css') || path.endsWith('.scss')) return 'css';
  if (path.endsWith('.html')) return 'html';
  if (path.endsWith('.md')) return 'markdown';
  if (path.endsWith('.yml') || path.endsWith('.yaml')) return 'yaml';
  return 'plaintext';
};

export function CodeViewer({ artifact, isSelected = false, onSelect }: CodeViewerProps) {
  const [isCopied, setIsCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(isSelected);

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.content);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const language = getLanguageFromPath(artifact.path);
  const lineCount = artifact.content.split('\n').length;
  const previewLines = artifact.content.split('\n').slice(0, 3).join('\n');

  return (
    <div className="rounded-lg border border-white/10 bg-slate-950 overflow-hidden">
      <button
        onClick={() => {
          setIsExpanded(!isExpanded);
          onSelect?.();
        }}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-900/50 transition-colors"
      >
        <div className="flex items-center gap-2 flex-1 min-w-0 text-left">
          <FileCode className="h-4 w-4 text-blue-400 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-slate-200 truncate">{artifact.path}</p>
            <p className="text-xs text-slate-400">
              {artifact.kind} • {lineCount} lines
            </p>
          </div>
        </div>
        <ChevronDown
          className={`h-4 w-4 text-slate-400 flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>

      {isExpanded && (
        <div className="border-t border-white/10">
          <div className="flex items-center justify-between px-4 py-2 bg-slate-900/30 border-b border-white/5">
            <span className="text-xs font-mono text-slate-400">{language}</span>
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 px-2 py-1 rounded text-xs text-slate-300 hover:bg-slate-800 transition-colors"
            >
              {isCopied ? (
                <>
                  <Check className="h-3 w-3" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  Copy
                </>
              )}
            </button>
          </div>

          <pre className="p-4 overflow-x-auto font-mono text-xs text-slate-300 max-h-96">
            <code className="text-slate-300">{artifact.content}</code>
          </pre>
        </div>
      )}
    </div>
  );
}

interface ArtifactListProps {
  artifacts: ArtifactRecord[];
  isLoading?: boolean;
}

export function ArtifactList({ artifacts, isLoading = false }: ArtifactListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(artifacts[0]?.id || null);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-12 rounded-lg bg-slate-900/50 animate-pulse" />
        ))}
      </div>
    );
  }

  if (artifacts.length === 0) {
    return (
      <div className="rounded-lg border border-white/10 bg-slate-950 p-8 text-center">
        <FileCode className="h-8 w-8 mx-auto mb-2 text-slate-500" />
        <p className="text-slate-400">No artifacts generated yet</p>
      </div>
    );
  }

  // Group artifacts by kind
  const grouped = artifacts.reduce(
    (acc, artifact) => {
      const kind = artifact.kind || 'other';
      if (!acc[kind]) acc[kind] = [];
      acc[kind].push(artifact);
      return acc;
    },
    {} as Record<string, ArtifactRecord[]>,
  );

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([kind, items]) => (
        <div key={kind} className="space-y-2">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide px-1">
            {kind}
          </h3>
          <div className="space-y-2">
            {items.map((artifact) => (
              <CodeViewer
                key={artifact.id}
                artifact={artifact}
                isSelected={expandedId === artifact.id}
                onSelect={() => setExpandedId(expandedId === artifact.id ? null : artifact.id)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
