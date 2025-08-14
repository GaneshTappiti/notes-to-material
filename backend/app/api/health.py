"""Health check endpoints for deployment readiness monitoring."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os

router = APIRouter()

@router.get("/health/live")
async def health_live():
    """Liveness probe - always returns ok if service is running."""
    return {"status": "ok", "checks": {"basic": "ok"}}

@router.get("/health/ready")
async def health_ready():
    """Readiness probe - checks all dependencies are available."""
    checks = {}
    overall_status = "ok"
    status_code = 200

    # Check database connection
    try:
        from ..models import get_session, create_db
        create_db()
        with get_session() as session:
            # Simple query to verify DB is accessible
            session.execute("SELECT 1")
            checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {str(e)}"
        overall_status = "error"
        status_code = 503

    # Check vector store availability
    try:
        from ..services.vector_store import VECTOR_STORE
        # Simple test - check if vector store is initialized
        if hasattr(VECTOR_STORE, 'collection') and VECTOR_STORE.collection is not None:
            checks["vector_store"] = "ok"
        else:
            checks["vector_store"] = "not_initialized"
            overall_status = "degraded"
    except Exception as e:
        checks["vector_store"] = f"error: {str(e)}"
        overall_status = "degraded"  # Vector store issues shouldn't block readiness

    # Check Gemini API key presence
    try:
        from ..settings import settings
        if settings.GOOGLE_API_KEY and len(settings.GOOGLE_API_KEY.strip()) > 0:
            checks["gemini"] = "ok"
        else:
            checks["gemini"] = "missing"
            # Don't fail readiness if offline fallback is available
            if overall_status == "ok":
                overall_status = "degraded"
    except Exception as e:
        checks["gemini"] = f"error: {str(e)}"
        if overall_status == "ok":
            overall_status = "degraded"

    response_data = {
        "status": overall_status,
        "checks": checks
    }

    return JSONResponse(content=response_data, status_code=status_code)
