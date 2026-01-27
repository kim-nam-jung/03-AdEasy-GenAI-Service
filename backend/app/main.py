from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import logging

logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Explicitly allow all for debugging/cloud access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

from app.api.routes import ws

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws.router, tags=["websocket"])

# Mount outputs directory
# /app/outputs inside Docker (cwd is /app)
OUTPUTS_DIR = Path("/app/outputs")
if not OUTPUTS_DIR.exists():
    OUTPUTS_DIR = Path("outputs") # Fallback for local dev if not in docker root
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}
