from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalResponse)
async def search(request: RetrievalRequest, db: Session = Depends(get_db)) -> RetrievalResponse:
    hits = await RetrievalService(db).search(request.query, request.top_k)
    return RetrievalResponse(query=request.query, hits=hits)
