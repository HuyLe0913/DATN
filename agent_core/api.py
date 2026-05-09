import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import asyncio
import os
from dotenv import load_dotenv

from agent.orchestrator import Agent
from schemas.agent import AgentRequest

load_dotenv()

app = FastAPI(title="Financial Agent API Server", version="1.0.0")

# Global agent instance
financial_agent = None

@app.on_event("startup")
async def startup_agent():
    global financial_agent
    try:
        # Initialize agent pointing to its workspace
        workspace_path = Path(__file__).parent / "agent_workspace"
        financial_agent = Agent(workspace_base=str(workspace_path))
        
        # Load MCP configuration (to connect to the data tools in /backend)
        mcp_config = Path(__file__).parent / "mcp.json"
        if mcp_config.exists():
            await financial_agent.load_mcp_config(str(mcp_config))
        print(f"Financial Agent Server started. Workspace: {workspace_path}")
    except Exception as e:
        print(f"Failed to initialize Financial Agent: {e}")

class ChatRequest(BaseModel):
    messages: List[dict]
    pdfContext: Optional[str] = None
    pdfName: Optional[str] = None

@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    if not financial_agent:
        raise HTTPException(status_code=503, detail="Agent is not initialized")
    
    try:
        # Lấy tin nhắn cuối cùng của người dùng
        last_msg = request.messages[-1]
        user_message = last_msg.get("content", "")
        if not user_message and "parts" in last_msg:
            user_message = " ".join([
                p.get("text", "") for p in last_msg["parts"] 
                if p.get("type") == "text"
            ])
            
        # Chuẩn bị lịch sử tin nhắn (loại bỏ tin nhắn cuối cùng vì nó được truyền qua user_request)
        history = []
        for m in request.messages[:-1]:
            content = m.get("content", "")
            if not content and "parts" in m:
                content = " ".join([
                    p.get("text", "") for p in m["parts"] 
                    if p.get("type") == "text"
                ])
            history.append({"role": m.get("role"), "content": content})
        
        # Đính kèm PDF context nếu có vào tin nhắn cuối
        full_request_text = user_message
        if request.pdfContext:
            full_request_text = f"[Source PDF: {request.pdfName}]\n{request.pdfContext}\n\nUser Question: {user_message}"
        
        agent_req = AgentRequest(
            user_request=full_request_text,
            history=history,
            session_id="web-session"
        )
        
        async def wrapped_stream():
            async for chunk in financial_agent.process_request_stream(agent_req):
                print(f"DEBUG STREAM: {chunk.strip()}")
                yield chunk

        return StreamingResponse(
            wrapped_stream(),
            media_type="text/event-stream"
        )
    except Exception as e:
        print(f"Error in chat_with_agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    # This server runs on 8002 to distinguish from backend tools on 8001
    uvicorn.run("api:app", host="0.0.0.0", port=8002, reload=True)
