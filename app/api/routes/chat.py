import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatResponse)
async def query_chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    return await ChatService(db).answer(request.query, request.top_k, request.system_prompt)


@router.post("/stream")
async def stream_chat(request: ChatRequest, db: Session = Depends(get_db)) -> EventSourceResponse:
    sources, generator = await ChatService(db).stream_answer(
        request.query, request.top_k, request.system_prompt
    )

    async def event_generator():
        yield {"event": "sources", "data": json.dumps([source.model_dump() for source in sources])}
        async for chunk in generator:
            yield {"event": "token", "data": chunk}
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_generator())
