import logging
import asyncio
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from schemas.agent import AgentRequest, AgentResponse
from llm.orchestrator import LLMOrchestrator
from tools.manager import ToolManager
from tools.builtins.read import read_file
from tools.builtins.write import write_file
from tools.builtins.list_dir import list_dir
from tools.builtins.web_search import web_search
from tools.builtins.interpreter import python_interpreter
from tools.mcp.integration import MCPIntegrator
from infra.workspace import WorkspaceProvider
from agent.skill_loader import SkillLoader
from agent.policy_manager import PolicyManager

logger = logging.getLogger(__name__)

import os

class Agent:
    def __init__(
        self,
        workspace_base: str = "./workspace",
        model: Optional[str] = None,
        agent_id: str = "banking_agent"
    ):
        self.workspace_provider = WorkspaceProvider(workspace_base)
        self.tool_manager = ToolManager()
        self.agent_id = agent_id
        
        if not model:
            model = os.getenv("AGENT_MODEL_NAME", "openrouter/google/gemini-2.0-flash-lite:free")
            
        # Initialize Policy Manager
        self.policy_manager = PolicyManager(workspace_root="./agent_workspace")
        self.policy_manager.load_policy(agent_id=self.agent_id)
        
        # Initialize LLM Orchestrator
        model_name = os.getenv("AGENT_MODEL_NAME", "gpt-4o-mini")
        llmgate_base = os.getenv("LLMGATE_BASE_URL")
        llmgate_key = os.getenv("LLMGATE_API_KEY")
        
        self.llm_orchestrator = LLMOrchestrator(
            model=model_name,
            api_base=llmgate_base,
            api_key=llmgate_key
        )
        self.mcp_integrator = MCPIntegrator(self.tool_manager, self.policy_manager)
        
        # Initialize and load skills from hierarchical workspace
        self.skill_loader = SkillLoader(skills_root="./agent_workspace")
        self.skill_loader.load_all(agent_id=self.agent_id)
        self.messages: List[Dict[str, str]] = []
        
        self._register_builtin_tools()

    async def connect_mcp(self, url: str, name: str = "backend"):
        """Establish connection to an MCP server."""
        return await self.mcp_integrator.connect_and_register(url, name)

    async def load_mcp_config(self, config_path: str):
        """Load multiple MCP servers from a config file."""
        return await self.mcp_integrator.load_config(config_path)

    def _register_tool_safely(self, name: str, description: str, parameters: Dict[str, Any], func: Any):
        """Đăng ký tool nếu được chính sách cho phép."""
        if self.policy_manager.is_tool_allowed(name):
            self.tool_manager.register_tool(name, description, parameters, func)
        else:
            logger.info(f"Tool '{name}' is restricted by policy for agent {self.agent_id}")

    def _register_builtin_tools(self):
        """Đăng ký các công cụ tích hợp sẵn."""
        self._register_tool_safely(
            "read_file",
            "Đọc nội dung từ một tệp tin",
            {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            read_file
        )
        self._register_tool_safely(
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
        self._register_tool_safely(
            "list_dir",
            "Liệt kê các tệp và thư mục trong một đường dẫn",
            {"type": "object", "properties": {"path": {"type": "string", "default": "."}}},
            list_dir
        )
        self._register_tool_safely(
            "web_search",
            "Tìm kiếm thông tin trực thực tế trên internet (tin tức, giá thị trường...)",
            {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            web_search
        )
        self._register_tool_safely(
            "python_interpreter",
            "Chạy mã Python để tính toán tài chính hoặc xử lý dữ liệu phức tạp",
            {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]},
            python_interpreter
        )

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        start_time = time.time()
        from datetime import datetime
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        workspace_root = self.workspace_provider.get_workspace_root(
            user_id="default", agent_id="agent_1"
        )
        
        skills_context = self.skill_loader.get_skills_summary()
        
        # Load AGENT.md persona
        persona = "Bạn là một Trợ lý AI Tài chính chuyên nghiệp."
        agent_md_path = Path("./agent_workspace") / self.agent_id / "AGENT.md"
        if agent_md_path.exists():
            persona = agent_md_path.read_text(encoding="utf-8")
        
        available_tools = list(self.tool_manager.tools.keys())
        
        system_prompt = f"""{persona}

Hôm nay là ngày: {current_date}.
Thư mục làm việc của bạn tại: {workspace_root}. 

{skills_context}

Bạn có các công cụ sau để tương tác với môi trường: {', '.join(available_tools)}.
Bạn PHẢI sử dụng các công cụ này để thu thập đầy đủ dữ liệu trước khi đưa ra câu trả lời cuối cùng.
QUY TẮC TRUY VẤN: Trong tham số `query`, TUYỆT ĐỐI KHÔNG dùng cả câu dài. Chỉ dùng các TỪ KHÓA chuyên môn (ví dụ: "NIM", "CASA").
KỶ LUẬT CÔNG CỤ: Bạn chỉ có ngân sách tối đa 2 LẦN gọi `python_interpreter` cho mỗi yêu cầu. Hãy gộp tất cả các phép tính vào ít lượt nhất có thể.
QUY TẮC SONG SONG: Bạn có thể gọi song song các truy vấn, nhưng KHÔNG ĐƯỢC vượt quá 5 truy vấn trong một lượt gọi tool để tránh làm loãng ngữ cảnh. Hãy chọn lọc những từ khóa quan trọng nhất trước.
KHÔNG ĐƯỢC dừng lại hoặc hỏi ý kiến nếu chưa có đủ số liệu. Phải kiên trì nếu chưa tìm thấy kết quả.
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

    async def process_request_stream(self, request: AgentRequest):
        """Xử lý yêu cầu và trả về luồng dữ liệu (thoughts + final result)."""
        workspace_root = self.workspace_provider.get_workspace_root(
            user_id="default", agent_id="agent_1"
        )
        skills_context = self.skill_loader.get_skills_summary()
        from datetime import datetime
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        # Load AGENT.md persona
        persona = "Bạn là một Trợ lý AI Tài chính chuyên nghiệp."
        agent_md_path = Path("./agent_workspace") / self.agent_id / "AGENT.md"
        if agent_md_path.exists():
            persona = agent_md_path.read_text(encoding="utf-8")
        
        available_tools = list(self.tool_manager.tools.keys())
        system_prompt = f"""{persona}

Hôm nay là ngày: {current_date}.
Thư mục làm việc của bạn tại: {workspace_root}. 

{skills_context}

Bạn có các công cụ sau để tương tác với môi trường: {', '.join(available_tools)}.
Bạn PHẢI sử dụng các công cụ này để thu thập đầy đủ dữ liệu trước khi đưa ra câu trả lời cuối cùng.
QUY TẮC TRUY VẤN: Trong tham số `query`, TUYỆT ĐỐI KHÔNG dùng cả câu dài. Chỉ dùng các TỪ KHÓA chuyên môn (ví dụ: "NIM", "CASA").
KỶ LUẬT CÔNG CỤ: Bạn chỉ có ngân sách tối đa 2 LẦN gọi `python_interpreter` cho mỗi yêu cầu. Hãy gộp tất cả các phép tính vào ít lượt nhất có thể.
QUY TẮC SONG SONG: Bạn có thể gọi song song các truy vấn, nhưng KHÔNG ĐƯỢC vượt quá 5 truy vấn trong một lượt gọi tool để tránh làm loãng ngữ cảnh. Hãy chọn lọc những từ khóa quan trọng nhất trước.
KHÔNG ĐƯỢC dừng lại hoặc hỏi ý kiến nếu chưa có đủ số liệu. Phải kiên trì nếu chưa tìm thấy kết quả.
Hãy luôn phản hồi bằng tiếng Việt.
"""
        # Queue để chứa các thoughts
        queue = asyncio.Queue()

        async def on_thought(msg: str):
            await queue.put(msg)

        # Chạy Agent trong background
        async def run_agent():
            try:
                # Sử dụng history từ request nếu có, nếu không dùng history nội bộ
                chat_history = request.history if request.history is not None else self.messages
                
                res = await self.llm_orchestrator.execute_with_tools(
                    system_prompt=system_prompt,
                    user_input=request.user_request,
                    tools=self.tool_manager.list_tools(),
                    context={"tool_manager": self.tool_manager, "workspace_root": workspace_root},
                    initial_messages=chat_history,
                    on_thought=on_thought
                )
                # Lưu vào history
                self.messages.append({"role": "user", "content": request.user_request})
                self.messages.append({"role": "assistant", "content": res})
                await queue.put(None) # Signal kết thúc
                return res
            except Exception as e:
                logger.exception(f"Error in run_agent: {e}")
                await queue.put(f"❌ Lỗi: {str(e)}")
                await queue.put(None)
                return str(e)

        agent_task = asyncio.create_task(run_agent())

        # Yield từ queue
        while True:
            msg = await queue.get()
            if msg is None:
                break
            yield f"THOUGHT: {msg}\n"
        
        # Lấy kết quả cuối cùng
        final_result = await agent_task
        yield f"FINAL: {final_result}"
