from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AgentRequest(BaseModel):
    request_id: Optional[str] = None
    session_id: Optional[str] = "default"
    user_request: str
    history: Optional[List[Dict[str, str]]] = None
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    request_id: str
    result: str
    processing_time: float

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]

class ToolResult(BaseModel):
    call_id: str
    output: Any
