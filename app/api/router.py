from fastapi import APIRouter

from app.api.routes import chat, documents, retrieval, tasks

api_router = APIRouter()
api_router.include_router(documents.router)
api_router.include_router(tasks.router)
api_router.include_router(retrieval.router)
api_router.include_router(chat.router)
