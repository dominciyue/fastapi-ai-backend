from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.models import Document, DocumentStatus, IndexingTask, TaskStatus
from app.schemas.document import DocumentResponse, IndexRequest, UploadResponse
from app.schemas.task import TaskResponse
from app.services.storage import save_upload_file

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required.")
    path = save_upload_file(file)
    document = Document(
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        storage_path=str(path),
        status=DocumentStatus.uploaded,
        metadata_={"suffix": Path(file.filename).suffix.lower()},
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return UploadResponse(document=DocumentResponse.model_validate(document, from_attributes=True))


@router.post("/index", response_model=TaskResponse)
async def queue_indexing(request: IndexRequest, db: Session = Depends(get_db)) -> TaskResponse:
    document = db.get(Document, request.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    task = IndexingTask(document_id=document.id, status=TaskStatus.queued, detail="Task queued.")
    db.add(task)
    db.commit()
    db.refresh(task)

    celery_task = celery_app.send_task("app.tasks.index_document", args=[str(task.id)])
    task.celery_task_id = celery_task.id
    document.status = DocumentStatus.indexing
    db.commit()
    db.refresh(task)

    return TaskResponse.model_validate(task, from_attributes=True)
