from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config.database import Base, engine
from app.config.settings import get_settings
from app.models import casefile, logs, metadata, report, scraped_case, user  # noqa: F401
from app.routes.admin_routes import router as admin_router
from app.routes.auth_routes import router as auth_router
from app.routes.upload_routes import router as upload_router
from app.routes.precedent_routes import router as precedent_router

try:
    from app.routes.report_routes import router as report_router
except Exception:
    report_router = None

try:
    from app.routes.search_routes import router as search_router
except Exception:
    search_router = None


settings = get_settings()
app = FastAPI(title=settings.PROJECT_NAME)

# Allow local frontend apps to call backend APIs during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(upload_router, prefix=settings.API_V1_PREFIX)
app.include_router(precedent_router, prefix=settings.API_V1_PREFIX)

if report_router is not None:
    app.include_router(report_router, prefix=settings.API_V1_PREFIX)

if search_router is not None:
    app.include_router(search_router, prefix=settings.API_V1_PREFIX)

storage_root = Path("backend/storage")
casefiles_dir = storage_root / "casefiles"
reports_dir = storage_root / "reports"
casefiles_dir.mkdir(parents=True, exist_ok=True)
reports_dir.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_root)), name="storage")
app.mount("/reports", StaticFiles(directory=str(reports_dir)), name="reports")


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.PROJECT_NAME}
