import json
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from backend.app.services.chat_agent import process_chat_message

router = APIRouter(prefix="/chat", tags=["AI Chatbot"])

class ChatMessageRequest(BaseModel):
    message: str
    destination_slug: Optional[str] = None  # None = let AI decide from message context
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class ChatCard(BaseModel):
    emoji: str
    title: str
    subtitle: str

class ChatMessageResponse(BaseModel):
    text: str
    cards: List[ChatCard] = Field(default_factory=list)

@router.post("", response_model=ChatMessageResponse)
async def chat_endpoint(req: ChatMessageRequest):
    result = await process_chat_message(
        user_message=req.message,
        destination_slug=req.destination_slug,
        history=req.history
    )
    return ChatMessageResponse(**result)

@router.post("/stream")
async def chat_stream_endpoint(req: ChatMessageRequest):
    result = await process_chat_message(
        user_message=req.message,
        destination_slug=req.destination_slug,
        history=req.history
    )

    async def token_generator():
        # Stream text words progressively
        words = result["text"].split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0.03)

        # Emit cards at the end
        yield f"data: {json.dumps({'cards': result['cards'], 'done': True})}\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
