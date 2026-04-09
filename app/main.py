from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.exceptions import AppError
from app.core.health import check_database_connection, check_redis_connection
from app.core.logging import setup_logging
from app.core.metrics import metrics_store

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="A FastAPI RAG backend designed to integrate with Dify workflows and tools.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    started_at = perf_counter()
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        latency_ms = int((perf_counter() - started_at) * 1000)
        metrics_store.record_http_request(request.url.path, 500, latency_ms)
        raise

    latency_ms = int((perf_counter() - started_at) * 1000)
    metrics_store.record_http_request(request.url.path, response.status_code, latency_ms)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(latency_ms)
    return response


def _error_payload(
    request: Request,
    *,
    detail: str,
    error_code: str,
    retryable: bool,
) -> dict[str, object]:
    return {
        "detail": detail,
        "error_code": error_code,
        "retryable": retryable,
        "request_id": getattr(request.state, "request_id", "unknown"),
    }


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            request,
            detail=exc.message,
            error_code=exc.error_code,
            retryable=exc.retryable,
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            request,
            detail=str(exc),
            error_code="validation_error",
            retryable=False,
        ),
    )


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> dict[str, object]:
    return metrics_store.snapshot()


@app.get("/health/ready", response_model=None)
async def readiness_check():
    checks = {
        "database": check_database_connection(),
        "redis": check_redis_connection(),
    }

    if all(checks.values()):
        return {"status": "ok", "checks": checks}

    return JSONResponse(status_code=503, content={"status": "degraded", "checks": checks})


app.include_router(api_router, prefix=settings.api_prefix)
