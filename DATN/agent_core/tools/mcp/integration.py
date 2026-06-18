import json
import os
import aiohttp
import logging
from typing import Any, Dict, List, Callable
from fastmcp import Client

logger = logging.getLogger(__name__)

class MCPIntegrator:
    def __init__(self, tool_manager, policy_manager=None):
        self.tool_manager = tool_manager
        self.policy_manager = policy_manager
        self.clients: Dict[str, Client] = {}

    async def load_config(self, config_path: str):
        """Load MCP servers from a JSON config file."""
        if not os.path.exists(config_path):
            logger.warning(f"MCP config file not found: {config_path}")
            return False
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            servers = config.get("servers", [])
            success_count = 0
            for server in servers:
                name = server.get("name")
                url = server.get("url")
                if name and url:
                    if await self.connect_and_register(url, name):
                        success_count += 1
            
            return success_count > 0
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            return False

    async def connect_and_register(self, url: str, name: str = "backend"):
        """Connect to an MCP SSE server and register its tools."""
        try:
            logger.info(f"Đang kết nối tới MCP server tại {url}...")
            client = Client(url)
            
            # Manually enter the context manager to keep the connection alive
            await client.__aenter__()
            
            self.clients[name] = client
            tools = await client.list_tools()
            for tool in tools:
                tool_name = f"mcp_{name}_{tool.name}"
                
                # Check policy if available
                if self.policy_manager and not self.policy_manager.is_tool_allowed(tool_name):
                    logger.info(f"MCP Tool '{tool_name}' is restricted by policy.")
                    continue
                
                def make_handler(c, tn):
                    async def h(**kwargs):
                        return await c.call_tool(tn, arguments=kwargs)
                    return h

                self.tool_manager.register_tool(
                    name=tool_name,
                    description=f"[MCP:{name}] {tool.description}",
                    parameters=tool.input_schema if hasattr(tool, "input_schema") else tool.inputSchema,
                    handler=make_handler(client, tool.name)
                )
            
            return True
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            msg = f"Failed to integrate MCP server {url}: {type(e).__name__}: {str(e)}"
            if "TaskGroup" in msg:
                 msg += " (Check if server is reachable and supports SSE)"
            logger.error(f"{msg}\nFull Traceback:\n{error_details}")
            
            # If it's a TaskGroup-like error, try to log the sub-exceptions
            if hasattr(e, "__exceptions__"):
                for i, sub_e in enumerate(e.__exceptions__):
                    logger.error(f"  Sub-exception {i+1}: {type(sub_e).__name__}: {sub_e}")
                    logger.error(f"  Sub-traceback:\n{''.join(traceback.format_exception(type(sub_e), sub_e, sub_e.__traceback__))}")
            
            return False

    async def close_all(self):
        """Clean up all MCP client connections."""
        for name, client in self.clients.items():
            try:
                await client.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing MCP client {name}: {e}")
        self.clients.clear()
