'use client';

import { CheckCircle, AlertCircle, Loader, Clock } from 'lucide-react';

interface ExecutionTimelineProps {
  events: Array<{
    id: string;
    timestamp: string;
    type: 'agent' | 'artifact' | 'error' | 'milestone';
    title: string;
    description?: string;
    status: 'completed' | 'running' | 'failed';
  }>;
}

export function ExecutionTimeline({ events }: ExecutionTimelineProps) {
  const getIcon = (type: string, status: string) => {
    if (status === 'running') {
      return <Loader className="w-4 h-4 text-blue-400 animate-spin" />;
    }
    if (status === 'failed') {
      return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
    switch (type) {
      case 'artifact':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'milestone':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      default:
        return <CheckCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-3 p-4">
      <h3 className="font-semibold text-white text-sm mb-4">Execution Timeline</h3>
      <div className="space-y-4">
        {events.map((event, index) => (
          <div key={event.id} className="flex gap-3">
            {/* Timeline line */}
            <div className="flex flex-col items-center">
              {getIcon(event.type, event.status)}
              {index < events.length - 1 && <div className="w-0.5 h-8 bg-slate-700 mt-2" />}
            </div>
            {/* Content */}
            <div className="pb-2">
              <p className="text-sm font-medium text-white">{event.title}</p>
              {event.description && <p className="text-xs text-slate-400 mt-1">{event.description}</p>}
              <p className="text-xs text-slate-500 mt-1">{event.timestamp}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
