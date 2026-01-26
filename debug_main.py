from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.api import api_router
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Exception Handler for 422
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = exc.errors()
    settings_cors = settings.BACKEND_CORS_ORIGINS
    
    logger.error("="*60)
    logger.error("❌ REQUEST VALIDATION ERROR (422)")
    logger.error(f"URL: {request.url}")
    logger.error(f"Method: {request.method}")
    logger.error(f"Headers: {request.headers}")
    logger.error(f"Errors: {error_details}")
    try:
        body = await request.body()
        logger.error(f"Body (First 1000 bytes): {body[:1000]}")
    except:
        logger.error("Could not read body")
    logger.error("="*60)
    
    return JSONResponse(
        status_code=422,
        content={"detail": error_details, "body_preview": "Check server logs"},
    )

# CORS Configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
