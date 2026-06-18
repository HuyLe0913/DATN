from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import httpx
import os
from fastapi.responses import StreamingResponse

from database import get_db, init_db
from models import Chat, Message
from schemas import ChatCreate, ChatResponse, ChatWithMessages, MessageCreate, MessageResponse

app = FastAPI(title="Financial App Backend", version="1.0.0")

AGENT_URL = os.getenv("AGENT_URL", "http://agent-core:8002/api/chat")

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/api/chats", response_model=List[ChatResponse])
async def list_chats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chat).order_by(Chat.updated_at.desc()))
    return result.scalars().all()

@app.post("/api/chats", response_model=ChatResponse)
async def create_chat(chat: ChatCreate, db: AsyncSession = Depends(get_db)):
    new_chat = Chat(id=chat.id, title=chat.title) if chat.id else Chat(title=chat.title)
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    return new_chat

@app.get("/api/chats/{chat_id}", response_model=ChatWithMessages)
async def get_chat(chat_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chat).options(selectinload(Chat.messages)).where(Chat.id == chat_id)
    )
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return chat

@app.delete("/api/chats/{chat_id}", status_code=204)
async def delete_chat(chat_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    await db.delete(chat)
    await db.commit()
    return None

@app.post("/api/chats/{chat_id}/message")
async def send_message(
    chat_id: str, 
    msg: MessageCreate, 
    db: AsyncSession = Depends(get_db)
):
    # 1. Lưu tin nhắn của người dùng
    user_msg = Message(chat_id=chat_id, role=msg.role, content=msg.content)
    db.add(user_msg)
    await db.commit()

    # 2. Lấy lịch sử để gửi cho Agent
    history_result = await db.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())
    )
    all_messages = history_result.scalars().all()
    
    # 3. Gọi Agent Core
    async def stream_agent_response():
        full_response_content = ""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, read=600.0)) as client:
                async with client.stream(
                    "POST", 
                    AGENT_URL, 
                    json={
                        "messages": [
                            {"role": m.role, "content": m.content} for m in all_messages
                        ]
                    }
                ) as response:
                    async for chunk in response.aiter_bytes():
                        decoded_chunk = chunk.decode()
                        if "FINAL: " in decoded_chunk:
                            parts = decoded_chunk.split("FINAL: ")
                            if len(parts) > 1:
                                full_response_content += parts[1]
                        
                        yield chunk
            
            # 4. Sau khi stream xong, lưu tin nhắn của Assistant vào DB
            if full_response_content:
                assistant_msg = Message(
                    chat_id=chat_id, 
                    role="assistant", 
                    content=full_response_content.strip()
                )
                db.add(assistant_msg)
                
                # Cập nhật title nếu là tin nhắn đầu
                chat_result = await db.execute(select(Chat).where(Chat.id == chat_id))
                chat_obj = chat_result.scalars().first()
                if chat_obj and chat_obj.title == "New Chat":
                    chat_obj.title = msg.content[:30] + "..."
                
                await db.commit()
                
        except Exception as e:
            yield f"Error connecting to agent: {str(e)}".encode()

    return StreamingResponse(stream_agent_response(), media_type="text/event-stream")
