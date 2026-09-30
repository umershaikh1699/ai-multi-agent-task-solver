from __future__ import annotations

from typing import Any, Dict

from app.tools.base import ToolRegistry


class ToolAgent:
    type = "tool.agent"

    async def run(
        self, *, params: Dict[str, Any], inputs: Dict[str, Any], tools: ToolRegistry
    ) -> Dict[str, Any]:
        tool_name = params.get("tool")
        if not tool_name:
            raise ValueError("params.tool is required")
        tool = tools.create(tool_name)
        args = dict(params.get("args") or {})
        source = params.get("input_from")
        if source:
            args["data"] = inputs.get(source)
        return await tool.run(**args)
