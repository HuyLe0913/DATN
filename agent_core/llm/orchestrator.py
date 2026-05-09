import logging
import litellm
from typing import Any, Dict, List, Optional, Callable
from schemas.agent import ToolCall

logger = logging.getLogger(__name__)

class LLMOrchestrator:
    def __init__(self, model: str = "gpt-4o-mini", max_iterations: int = 12, api_base: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model
        self.max_iterations = max_iterations
        self.api_base = api_base
        self.api_key = api_key

    async def execute_with_tools(
        self,
        system_prompt: str,
        user_input: str,
        tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        initial_messages: Optional[List[Dict[str, str]]] = None,
        on_thought: Optional[Callable[[str], Any]] = None
    ) -> str:
        # Diagnostic log
        logger.info(f"LLM execute_with_tools: Model={self.model}, Tools={[t['function']['name'] for t in tools]}")
        
        messages = initial_messages or []
        if not any(m["role"] == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})

        for i in range(self.max_iterations):
            logger.info(f"---\nBắt đầu vòng lặp {i+1}...")
            if on_thought:
                await on_thought(f"Đang phân tích yêu cầu (lượt {i+1})...")
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                api_base=self.api_base,
                api_key=self.api_key
            )
            
            message = response.choices[0].message
            # Convert to dict for consistent history
            messages.append(message.model_dump() if hasattr(message, "model_dump") else message)

            if not message.tool_calls:
                logger.info(f"Không còn yêu cầu gọi công cụ. Đang hoàn tất...")
                return message.content or ""

            # Handle tool calls
            tool_manager = context.get("tool_manager")
            if not tool_manager:
                logger.error("ToolManager missing in context")
                return "Error: ToolManager missing"

            import asyncio
            
            async def run_and_append_tool(tc):
                logger.info(f"ĐANG THỰC THI CÔNG CỤ: {tc.function.name} với {tc.function.arguments}")
                if on_thought:
                    import json
                    args = {}
                    try:
                        args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                    except:
                        pass
                        
                    # Tạo nội dung thân thiện và chi tiết cho người dùng
                    msg = f"⚙️ Đang sử dụng công cụ {tc.function.name}..."
                    
                    if tc.function.name == "python_interpreter":
                        msg = "🧮 Đang thực hiện tính toán tài chính và phân tích số liệu..."
                    elif "search" in tc.function.name or "ask" in tc.function.name:
                        query = args.get("query") or args.get("question") or "dữ liệu"
                        msg = f"🔎 Đang tìm kiếm thông tin về: **{query}**"
                    elif tc.function.name == "read_file":
                        path = args.get("path") or "tệp tin"
                        msg = f"📄 Đang đọc dữ liệu từ tệp: `{path}`"
                    elif tc.function.name == "list_dir":
                        path = args.get("path") or "thư mục"
                        msg = f"📁 Đang kiểm tra danh sách tệp trong: `{path}`"
                    elif tc.function.name == "write_file":
                        path = args.get("path") or "tệp tin"
                        msg = f"📝 Đang lưu kết quả vào: `{path}`"
                        
                    await on_thought(msg)
                
                res = await tool_manager.call_tool(
                    tc.function.name,
                    tc.function.arguments
                )
                # Log tóm tắt ra console (agent_main)
                logger.info(f"KẾT QUẢ CÔNG CỤ: {tc.function.name} -> {str(res)[:100]}...")
                # Log đầy đủ vào file (full_audit)
                import logging
                import json
                
                # Chuyển đổi kết quả sang JSON string gọn gàng hơn cho log
                try:
                    if hasattr(res, 'model_dump'):
                        log_res = json.dumps(res.model_dump(), ensure_ascii=False)
                    else:
                        log_res = str(res)
                except Exception:
                    log_res = str(res)
                    
                logging.getLogger("full_audit").info(f"KẾT QUẢ CÔNG CỤ: {tc.function.name} -> {log_res}")
                return {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": str(res)
                }

            # Chạy song song tất cả các tool calls trong lượt này
            num_tools = len(message.tool_calls)
            if num_tools > 1:
                logger.info(f"Bắt đầu thực thi song song {num_tools} công cụ...")
            
            tool_results = await asyncio.gather(*[run_and_append_tool(tc) for tc in message.tool_calls])
            messages.extend(tool_results)
        
        return "Lỗi: Đạt giới hạn vòng lặp tối đa"
