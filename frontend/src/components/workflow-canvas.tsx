"use client";

import ReactFlow, { Background, Controls, MiniMap, type Edge, type Node } from 'reactflow';
import 'reactflow/dist/style.css';

const nodes: Node[] = [
  { id: '1', position: { x: 40, y: 100 }, data: { label: 'User Prompt' }, type: 'input' },
  { id: '2', position: { x: 250, y: 40 }, data: { label: 'Planner Agent' } },
  { id: '3', position: { x: 500, y: 150 }, data: { label: 'Architect Agent' } },
  { id: '4', position: { x: 760, y: 40 }, data: { label: 'Frontend Agent' } },
  { id: '5', position: { x: 760, y: 220 }, data: { label: 'Backend Agent' } },
  { id: '6', position: { x: 1030, y: 100 }, data: { label: 'Testing + Deploy' }, type: 'output' },
];

const edges: Edge[] = [
  { id: '1-2', source: '1', target: '2', animated: true },
  { id: '2-3', source: '2', target: '3', animated: true },
  { id: '3-4', source: '3', target: '4', animated: true },
  { id: '3-5', source: '3', target: '5', animated: true },
  { id: '4-6', source: '4', target: '6', animated: true },
  { id: '5-6', source: '5', target: '6', animated: true },
];

export function WorkflowCanvas() {
  return (
    <div className="h-[620px] overflow-hidden rounded-[2rem] border border-white/10 bg-slate-950/60 shadow-glow">
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background gap={18} color="rgba(148, 163, 184, 0.18)" />
        <Controls />
        <MiniMap zoomable pannable />
      </ReactFlow>
    </div>
  );
}
