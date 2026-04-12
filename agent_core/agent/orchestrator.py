import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from schemas.agent import AgentRequest, AgentResponse
from llm.orchestrator import LLMOrchestrator
from tools.manager import ToolManager
from tools.builtins.file_ops import read_file, write_file, list_dir
from tools.mcp.integration import MCPIntegrator
from infra.workspace import WorkspaceProvider

logger = logging.getLogger(__name__)

import os

class Agent:
    def __init__(
        self,
        workspace_base: str = "./workspace",
        model: Optional[str] = None
    ):
        self.workspace_provider = WorkspaceProvider(workspace_base)
        self.tool_manager = ToolManager()
        
        if not model:
            model = os.getenv("AGENT_MODEL_NAME", "openrouter/google/gemini-2.0-flash-lite:free")
            
        self.llm_orchestrator = LLMOrchestrator(model=model)
        self.mcp_integrator = MCPIntegrator(self.tool_manager)
        self.messages: List[Dict[str, str]] = []
        
        self._register_builtin_tools()

    async def connect_mcp(self, url: str, name: str = "backend"):
        """Establish connection to an MCP server."""
        return await self.mcp_integrator.connect_and_register(url, name)

    async def load_mcp_config(self, config_path: str):
        """Load multiple MCP servers from a config file."""
        return await self.mcp_integrator.load_config(config_path)

    def _register_builtin_tools(self):
        """Đăng ký các công cụ tích hợp sẵn."""
        self.tool_manager.register_tool(
            "read_file",
            "Đọc nội dung từ một tệp tin",
            {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            read_file
        )
        self.tool_manager.register_tool(
            "write_file",
            "Ghi nội dung vào một tệp tin",
            {
                "type": "object", 
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                }, 
                "required": ["path", "content"]
            },
            write_file
        )
        self.tool_manager.register_tool(
            "list_dir",
            "Liệt kê các tệp và thư mục trong một đường dẫn",
            {"type": "object", "properties": {"path": {"type": "string", "default": "."}}},
            list_dir
        )

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        start_time = time.time()
        from datetime import datetime
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        workspace_root = self.workspace_provider.get_workspace_root(
            user_id="default", agent_id="agent_1"
        )
        
        system_prompt = f"""Bạn là một Trợ lý AI hữu ích. 
Hôm nay là ngày: {current_date}.
Thư mục làm việc của bạn tại: {workspace_root}. 
Bạn có các công cụ để tương tác với môi trường: {', '.join(self.tool_manager.tools.keys())}.
Bạn PHẢI sử dụng các công cụ này bất cứ khi nào cần thiết để thực hiện yêu cầu của người dùng.
Không được đoán thông tin nếu có công cụ hỗ trợ. Hãy luôn kiểm tra dữ liệu qua công cụ trước khi trả lời.
Hãy luôn phản hồi bằng tiếng Việt.
"""
        
        result = await self.llm_orchestrator.execute_with_tools(
            system_prompt=system_prompt,
            user_input=request.user_request,
            tools=self.tool_manager.list_tools(),
            context={"tool_manager": self.tool_manager, "workspace_root": workspace_root},
            initial_messages=self.messages
        )
        
        self.messages.append({"role": "user", "content": request.user_request})
        self.messages.append({"role": "assistant", "content": result})
        
        processing_time = time.time() - start_time
        
        self.workspace_provider.append_log(
            workspace_root, 
            "audit.log", 
            f"[{request.session_id}] User: {request.user_request} | Assistant: {result}"
        )

        return AgentResponse(
            request_id=request.request_id or "root",
            result=result,
            processing_time=processing_time
        )
