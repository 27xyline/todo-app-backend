import logging
from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    CategoryNameConflictError,
    CategoryNotFoundError,
    TaskNotFoundError,
)
from app.core.logging import configure_logging

logger = logging.getLogger("app.middleware")
request_number = 0


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:
        global request_number

        request_number += 1
        current_request_number = request_number

        started_at = perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - started_at) * 1000
            logger.exception(
                "Request failed: %s %s completed_in=%.2fms",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        response.headers["X-Request-Number"] = str(current_request_number)

        duration_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "%s %s -> %s (%.2f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.exception_handler(TaskNotFoundError)
    async def task_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Задача не найдена"})

    @app.exception_handler(CategoryNotFoundError)
    async def category_not_found_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Категория не найдена"})

    @app.exception_handler(CategoryNameConflictError)
    async def category_conflict_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Категория с таким названием уже существует"},
        )

    app.include_router(api_router)
    return app


app = create_app()
