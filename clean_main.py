from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS Configuration
# settings.BACKEND_CORS_ORIGINS might be empty/invalid, so we fallback to * for now
# given the specific VM deployment environment issues.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import ws

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws.router, tags=["websocket"])

# Mount outputs directory
OUTPUTS_DIR = Path("/app/outputs")
if not OUTPUTS_DIR.exists():
    OUTPUTS_DIR = Path("outputs")
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}
