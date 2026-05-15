from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GraphNode:
    id: str
    type: str
    config: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class GraphEdge:
    source: str
    target: str
    condition: str | None = None


@dataclass(slots=True)
class WorkflowGraph:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
