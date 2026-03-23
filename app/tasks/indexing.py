import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.indexing import IndexingService

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.index_document")
def index_document(task_id: str) -> str:
    db = SessionLocal()
    try:
        service = IndexingService(db)
        asyncio.run(service.run(task_id))
        return task_id
    except Exception:  # noqa: BLE001
        logger.exception("Document indexing failed for task %s", task_id)
        raise
    finally:
        db.close()
