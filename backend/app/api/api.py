from fastapi import APIRouter
from app.api.routes import tasks, debug

api_router = APIRouter()
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])
