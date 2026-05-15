'use client';

import { useEffect, useRef } from 'react';
import { AlertCircle, CheckCircle, Loader, AlertTriangle } from 'lucide-react';

interface LogsViewerProps {
  logs: Array<{ type: string; message: string; timestamp: string }>;
}

export function LogsViewer({ logs }: LogsViewerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogColor = (type: string) => {
    switch (type) {
      case 'error':
        return 'text-red-400';
      case 'warning':
        return 'text-yellow-400';
      case 'success':
        return 'text-green-400';
      default:
        return 'text-slate-300';
    }
  };

  const getLogIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="w-4 h-4" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4" />;
      case 'success':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <Loader className="w-4 h-4" />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900">
      <div className="bg-slate-800 border-b border-slate-700 px-4 py-2">
        <h3 className="text-sm font-semibold text-white">Execution Logs</h3>
      </div>
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-sm space-y-1"
      >
        {logs.map((log, index) => (
          <div key={index} className="flex gap-2 items-start">
            <span className={`flex-shrink-0 ${getLogColor(log.type)}`}>
              {getLogIcon(log.type)}
            </span>
            <span className="text-slate-500 text-xs">{log.timestamp}</span>
            <span className={getLogColor(log.type)}>{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
