from app.core.celery_app import celery_app
from app.tasks import indexing  # noqa: F401

__all__ = ["celery_app"]
