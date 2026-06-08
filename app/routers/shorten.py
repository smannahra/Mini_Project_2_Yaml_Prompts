from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import BlockedUrlError, InvalidUrlError
from app.limiter import limiter
from app.schemas import ShortenRequest, ShortenResponse
from app.services.url_service import shorten_url

router = APIRouter()


@router.post("/api/shorten")
@limiter.limit("100/hour")
async def shorten(
    request: Request,
    body: ShortenRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    # Fix 6: reject expiry dates in the past
    if body.expiry_date is not None:
        expiry = body.expiry_date
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry <= datetime.now(timezone.utc):
            return JSONResponse(
                status_code=422,
                content={"error": "expiry_date must be in the future", "code": "INVALID_EXPIRY"},
            )

    # Fix 5: typed exception classes — no string-matching to distinguish 422 vs 400
    try:
        record, is_new = shorten_url(db, body.url, body.expiry_date)
    except InvalidUrlError as exc:
        return JSONResponse(status_code=422, content={"error": str(exc), "code": "INVALID_URL"})
    except BlockedUrlError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc), "code": "MALICIOUS_URL"})
    # Fix 2: handle DB-level race condition and code-generation exhaustion
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            status_code=503,
            content={"error": "Service temporarily unavailable, please retry", "code": "COLLISION_ERROR"},
        )
    except RuntimeError as exc:
        return JSONResponse(
            status_code=503,
            content={"error": str(exc), "code": "CODE_GENERATION_FAILED"},
        )

    base = str(request.base_url).rstrip("/")
    payload = ShortenResponse(
        short_code=record.short_code,
        short_url=f"{base}/{record.short_code}",
        url=record.original_url,
        created_at=record.created_at,
        expiry_date=record.expiry_date,
    )
    http_status = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
    return JSONResponse(status_code=http_status, content=payload.model_dump(mode="json"))
