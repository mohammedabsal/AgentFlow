from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class Tool(Protocol):
    name: str

    def run(self, input_payload: dict[str, object]) -> dict[str, object]: ...


@dataclass
class ToolRegistry:
    tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self.tools[name]
