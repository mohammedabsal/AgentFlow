'use client';

import { ExternalLink } from 'lucide-react';

interface LivePreviewProps {
  artifacts: Array<{ id: string; path: string; content: string; language: string }>;
  selectedId: string | null;
}

export function LivePreview({ artifacts, selectedId }: LivePreviewProps) {
  const selectedArtifact = artifacts.find((a) => a.id === selectedId);

  if (!selectedArtifact) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <ExternalLink className="w-12 h-12 text-slate-600 mx-auto mb-2" />
          <p className="text-slate-400">No preview available</p>
        </div>
      </div>
    );
  }

  // Check if it's an HTML file that can be previewed
  if (selectedArtifact.path.endsWith('.html')) {
    return (
      <iframe
        srcDoc={selectedArtifact.content}
        className="flex-1 w-full h-full border-0"
        title="Preview"
      />
    );
  }

  // For other files, show a code preview
  return (
    <div className="flex-1 bg-slate-900 flex flex-col">
      <div className="bg-slate-800 border-b border-slate-700 p-3">
        <code className="text-sm text-slate-400">{selectedArtifact.path}</code>
      </div>
      <pre className="flex-1 overflow-auto p-4 text-sm text-slate-300 font-mono">
        {selectedArtifact.content}
      </pre>
    </div>
  );
}
