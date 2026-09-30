from __future__ import annotations

from typing import Any, Dict, Protocol

from app.tools.base import ToolRegistry


class AgentInterface(Protocol):
    type: str

    async def run(
        self, *, params: Dict[str, Any], inputs: Dict[str, Any], tools: ToolRegistry
    ) -> Dict[str, Any]:
        ...


class AgentFactory:
    def __init__(self) -> None:
        self._agents: Dict[str, type] = {}

    def add(self, cls: type) -> None:
        t = getattr(cls, "type", None)
        if not t:
            raise ValueError("Agent must define 'type'")
        self._agents[t] = cls

    def build(self, type_: str, **kwargs: Any) -> AgentInterface:
        if type_ not in self._agents:
            raise KeyError(f"Unknown agent type: {type_}")
        return self._agents[type_](**kwargs)

    def available(self) -> Dict[str, Any]:
        return {k: {"class": v.__name__} for k, v in self._agents.items()}
