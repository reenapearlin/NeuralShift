from fastapi import FastAPI

from app.config.database import Base, engine
from app.config.settings import get_settings
from app.models import casefile, logs, metadata, report, user  # noqa: F401
from app.routes.admin_routes import router as admin_router
from app.routes.auth_routes import router as auth_router


settings = get_settings()
app = FastAPI(title=settings.PROJECT_NAME)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.PROJECT_NAME}
