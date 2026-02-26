from fastapi import FastAPI
from app.routes import upload_routes
from app.routes import admin_routes
from app.routes import report_routes

app = FastAPI(title="Legal AI Backend")

app.include_router(upload_routes.router)
app.include_router(admin_routes.router)
app.include_router(report_routes.router)