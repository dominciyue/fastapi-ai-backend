from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk, DocumentStatus, IndexingTask, TaskStatus
from app.services.chunker import chunk_text
from app.services.document_parser import parse_document
from app.services.llm_client import OpenAICompatibleClient


class IndexingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.client = OpenAICompatibleClient()

    def mark_task(
        self, task_id: str, status: TaskStatus, detail: str | None = None
    ) -> IndexingTask:
        task = self.db.get(IndexingTask, UUID(task_id))
        if not task:
            raise ValueError(f"Task {task_id} not found.")
        task.status = status
        task.detail = detail
        self.db.commit()
        self.db.refresh(task)
        return task

    async def run(self, task_id: str) -> IndexingTask:
        task = self.mark_task(task_id, TaskStatus.started, "Indexing started.")
        document = self.db.get(Document, task.document_id)
        if not document:
            raise ValueError("Document not found.")

        try:
            document.status = DocumentStatus.indexing
            self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
            self.db.commit()

            text = parse_document(Path(document.storage_path))
            chunks = chunk_text(text)
            embeddings = await self.client.embed(chunks)

            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                self.db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        content=chunk,
                        metadata_={"source": document.filename, "chunk_index": index},
                        embedding=embedding,
                    )
                )

            document.chunk_count = len(chunks)
            document.status = DocumentStatus.indexed
            self.db.commit()
            return self.mark_task(task_id, TaskStatus.completed, f"Indexed {len(chunks)} chunks.")
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            document = self.db.get(Document, task.document_id)
            if document:
                document.status = DocumentStatus.failed
                document.error_message = str(exc)
                self.db.commit()
            return self.mark_task(task_id, TaskStatus.failed, str(exc))

    def get_task_with_document(self, task_id: str) -> tuple[IndexingTask, Document]:
        stmt = (
            select(IndexingTask, Document)
            .join(Document, Document.id == IndexingTask.document_id)
            .where(IndexingTask.id == UUID(task_id))
        )
        row = self.db.execute(stmt).one()
        return row[0], row[1]
