from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import IndexingTask
from app.schemas.task import TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)) -> TaskResponse:
    task = db.get(IndexingTask, UUID(task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return TaskResponse.model_validate(task, from_attributes=True)
