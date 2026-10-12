import logging

from fastapi import APIRouter, HTTPException, status

from app.core.database import check_database_connection

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def health_db() -> dict[str, str]:
    try:
        check_database_connection()
    except Exception:
        logger.exception("PostgreSQL health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "db": "unavailable"},
        ) from None
    return {"status": "ok"}
