from .base import ToolRegistry
from .http import GetHttp
from .jsonjq import Pick

def default_tool_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(GetHttp)
    reg.register(Pick)
    return reg