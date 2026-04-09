from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalResponse)
async def search(
    request: RetrievalRequest,
    http_request: Request,
    db: Session = Depends(get_db),
) -> RetrievalResponse:
    request_id = getattr(http_request.state, "request_id", "unknown")
    return await RetrievalService(db).search(request.query, request.top_k, request_id=request_id)
