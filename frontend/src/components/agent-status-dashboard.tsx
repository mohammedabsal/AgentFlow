'use client';

import { Loader, CheckCircle, AlertCircle, Zap } from 'lucide-react';

interface AgentStatusDashboardProps {
  logs: Array<{ type: string; message: string; timestamp: string }>;
}

export function AgentStatusDashboard({ logs }: AgentStatusDashboardProps) {
  const agents = [
    { name: 'Prompt Refinement Agent', status: 'pending' },
    { name: 'Planner Agent', status: 'pending' },
    { name: 'Architecture Agent', status: 'pending' },
    { name: 'Frontend Agent', status: 'pending' },
    { name: 'Backend Agent', status: 'pending' },
    { name: 'Database Agent', status: 'pending' },
    { name: 'Auth Agent', status: 'pending' },
    { name: 'DevOps Agent', status: 'pending' },
    { name: 'Integration Agent', status: 'pending' },
    { name: 'Testing Agent', status: 'pending' },
    { name: 'Self-Healing Agent', status: 'pending' },
    { name: 'Packaging Agent', status: 'pending' },
  ];

  // Update agent status based on logs
  logs.forEach((log) => {
    agents.forEach((agent) => {
      const message = log.message.toLowerCase();
      const agentName = agent.name.toLowerCase();
      const shortName = agentName.replace(' agent', '');
      if (message.includes(agentName) || message.includes(shortName)) {
        if (message.includes('completed') || message.includes('done')) {
          agent.status = 'completed';
        } else if (message.includes('error') || message.includes('failed')) {
          agent.status = 'error';
        } else if (message.includes('started') || message.includes('starting') || message.includes('running')) {
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
