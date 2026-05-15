'use client';

import { Loader, CheckCircle, AlertCircle, Zap } from 'lucide-react';

interface AgentStatusDashboardProps {
  logs: Array<{ type: string; message: string; timestamp: string }>;
}

export function AgentStatusDashboard({ logs }: AgentStatusDashboardProps) {
  // Extract unique agents from logs
  const agents = [
    { name: 'Prompt Refiner', status: 'active' },
    { name: 'Research Agent', status: 'pending' },
    { name: 'Planner', status: 'pending' },
    { name: 'Architect', status: 'pending' },
    { name: 'Frontend Agent', status: 'pending' },
    { name: 'Backend Agent', status: 'pending' },
    { name: 'Database Agent', status: 'pending' },
    { name: 'API Agent', status: 'pending' },
    { name: 'DevOps Agent', status: 'pending' },
    { name: 'Testing Agent', status: 'pending' },
    { name: 'Self-Healing Agent', status: 'pending' },
  ];

  // Update agent status based on logs
  logs.forEach((log) => {
    agents.forEach((agent) => {
      if (log.message.toLowerCase().includes(agent.name.toLowerCase())) {
        if (log.message.toLowerCase().includes('completed') || log.message.toLowerCase().includes('done')) {
          agent.status = 'completed';
        } else if (log.message.toLowerCase().includes('error') || log.message.toLowerCase().includes('failed')) {
          agent.status = 'error';
        } else if (log.message.toLowerCase().includes('starting') || log.message.toLowerCase().includes('running')) {
          agent.status = 'active';
        }
      }
    });
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Loader className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Zap className="w-4 h-4 text-slate-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-blue-400';
      case 'completed':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-slate-500';
    }
  };

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-white mb-3">Agent Status</h3>
      {agents.map((agent) => (
        <div key={agent.name} className="flex items-center gap-2 p-2 rounded hover:bg-slate-700">
          {getStatusIcon(agent.status)}
          <span className={`text-sm ${getStatusColor(agent.status)}`}>{agent.name}</span>
        </div>
      ))}
    </div>
  );
}
