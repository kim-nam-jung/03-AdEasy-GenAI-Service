from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key:
        return None # Allow for now
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return x_api_key
