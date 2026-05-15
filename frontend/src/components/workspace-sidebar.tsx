'use client';

import { ChevronDown, Folder, File, FolderOpen } from 'lucide-react';
import { useState } from 'react';

interface WorkspaceSidebarProps {
  projectName: string;
  artifacts: Array<{ id: string; path: string; language: string }>;
  selectedArtifact: string | null;
  onSelectArtifact: (id: string) => void;
}

export function WorkspaceSidebar({
  projectName,
  artifacts,
  selectedArtifact,
  onSelectArtifact,
}: WorkspaceSidebarProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  // Build file tree from artifacts
  const buildFileTree = () => {
    const tree: Record<string, any> = {};

    artifacts.forEach((artifact) => {
      const parts = artifact.path.split('/');
      let current = tree;

      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        if (i === parts.length - 1) {
          current[part] = { type: 'file', id: artifact.id, language: artifact.language };
        } else {
          if (!current[part]) {
            current[part] = { type: 'folder', children: {} };
          }
          current = current[part].children;
        }
      }
    });

    return tree;
  };

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const renderTree = (tree: Record<string, any>, prefix: string = ''): JSX.Element[] => {
    return Object.entries(tree).map(([name, item]) => {
      const path = prefix ? `${prefix}/${name}` : name;

      if (item.type === 'file') {
        const isSelected = item.id === selectedArtifact;
        return (
          <div
            key={path}
            className={`flex items-center gap-2 px-3 py-2 cursor-pointer rounded text-sm ${
              isSelected ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-700'
            }`}
            onClick={() => onSelectArtifact(item.id)}
          >
            <File className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">{name}</span>
          </div>
        );
      }

      if (item.type === 'folder') {
        const isExpanded = expandedFolders.has(path);
        return (
          <div key={path}>
            <div
              className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-slate-700 rounded text-sm text-slate-300"
              onClick={() => toggleFolder(path)}
            >
              <ChevronDown
                className={`w-4 h-4 flex-shrink-0 transition-transform ${!isExpanded ? '-rotate-90' : ''}`}
              />
              {isExpanded ? (
                <FolderOpen className="w-4 h-4 flex-shrink-0" />
              ) : (
                <Folder className="w-4 h-4 flex-shrink-0" />
              )}
              <span>{name}</span>
            </div>
            {isExpanded && item.children && (
              <div className="ml-2 border-l border-slate-700">
                {renderTree(item.children, path)}
              </div>
            )}
          </div>
        );
      }

      return null;
    });
  };

  const fileTree = buildFileTree();

  return (
    <div className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <h2 className="font-semibold text-white text-sm">{projectName || 'Workspace'}</h2>
        <p className="text-xs text-slate-400 mt-1">
          {artifacts.length} file{artifacts.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* File Tree */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {artifacts.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            <Folder className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No files generated yet</p>
          </div>
        ) : (
          renderTree(fileTree)
        )}
      </div>
    </div>
  );
}
