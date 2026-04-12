import logging
import litellm
from typing import Any, Dict, List, Optional
from schemas.agent import ToolCall

logger = logging.getLogger(__name__)

class LLMOrchestrator:
    def __init__(self, model: str = "gpt-4o-mini", max_iterations: int = 5):
        self.model = model
        self.max_iterations = max_iterations

    async def execute_with_tools(
        self,
        system_prompt: str,
        user_input: str,
        tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        initial_messages: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        # Diagnostic log
        logger.info(f"LLM execute_with_tools: Model={self.model}, Tools={[t['function']['name'] for t in tools]}")
        
        messages = initial_messages or []
        if not any(m["role"] == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})

        for i in range(self.max_iterations):
            print(f"---\nBắt đầu vòng lặp {i+1}...")
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
            )
            
            message = response.choices[0].message
            # Convert to dict for consistent history
            messages.append(message.model_dump() if hasattr(message, "model_dump") else message)

            if not message.tool_calls:
                print(f"Không còn yêu cầu gọi công cụ. Đang hoàn tất...")
                return message.content or ""

            # Handle tool calls
            tool_manager = context.get("tool_manager")
            if not tool_manager:
                logger.error("ToolManager missing in context")
                return "Error: ToolManager missing"

            for tool_call in message.tool_calls:
                print(f"ĐANG THI CÔNG CỤ: {tool_call.function.name} với {tool_call.function.arguments}")
                result = await tool_manager.call_tool(
                    tool_call.function.name,
                    tool_call.function.arguments
                )
                print(f"KẾT QUẢ CÔNG CỤ: {str(result)[:100]}...")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": str(result)
                })
        
        return "Lỗi: Đạt giới hạn vòng lặp tối đa"
