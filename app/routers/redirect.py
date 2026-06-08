import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analytics_service import record_click
from app.services.url_service import lookup_url

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{short_code}")
async def redirect(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    url = lookup_url(db, short_code)
    if not url:
        return JSONResponse(
            status_code=404,
            content={"error": "Short code not found", "code": "NOT_FOUND"},
        )
    if url.expiry_date and url.expiry_date < datetime.utcnow():
        return JSONResponse(
            status_code=410,
            content={"error": "URL has expired", "code": "URL_EXPIRED"},
        )

    referrer = request.headers.get("referer") or None
    # Fix 3: analytics failure must never block the redirect (NFR-004 availability)
    try:
        record_click(db, url, referrer)
    except Exception:
        logger.exception("Analytics write failed for short_code=%s", short_code)

    return RedirectResponse(url=url.original_url, status_code=302)
