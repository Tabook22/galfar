from contextlib import asynccontextmanager
import threading

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.exceptions import AppError
from app.routers import analysis, batches, chat, reports, saved_analyses
from app.routers import settings as settings_router
from app.services.persistence_service import PersistenceService

app_settings = get_settings()


def _run_startup_sync() -> None:
    from app.database import SessionLocal

    current = get_settings()
    db = SessionLocal()
    try:
        PersistenceService(current).sync_all(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings.cache_clear()
    init_db()
    current = get_settings()
    current.upload_path.mkdir(parents=True, exist_ok=True)
    current.saved_analyses_path.mkdir(parents=True, exist_ok=True)

    # Don't block the server from accepting requests while reconciling storage.
    threading.Thread(target=_run_startup_sync, daemon=True).start()

    yield


app = FastAPI(title=app_settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(reports.router, prefix="/api")
app.include_router(batches.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(saved_analyses.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")


@app.get("/api/health")
def health_check():
    current = get_settings()
    return {
        "status": "ok",
        "app": current.app_name,
        "llm_enabled": current.llm_ready,
    }
