import logging
import json
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

class ToolManager:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable):
        self.tools[name] = {
            "info": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                }
            },
            "handler": handler
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        return [t["info"] for t in self.tools.values()]

    async def call_tool(self, name: str, arguments: Any) -> Any:
        if name not in self.tools:
            return f"Error: Tool {name} not found"
        
        if isinstance(arguments, str):
            try:
                args = json.loads(arguments)
            except:
                args = {}
        else:
            args = arguments

        logger.info(f"Calling tool {name} with args {args}")
        try:
            handler = self.tools[name]["handler"]
            result = handler(**args)
            
            import asyncio
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return f"Error: {str(e)}"
