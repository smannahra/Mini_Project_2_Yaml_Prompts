from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AnalyticsResponse, UrlDetailResponse
from app.services.analytics_service import get_analytics
from app.services.url_service import delete_url, lookup_url

router = APIRouter(prefix="/api/urls")

_NOT_FOUND = {"error": "Short code not found", "code": "NOT_FOUND"}


@router.get("/{short_code}/analytics")
async def get_url_analytics(short_code: str, db: Session = Depends(get_db)):
    data = get_analytics(db, short_code)
    if data is None:
        return JSONResponse(status_code=404, content=_NOT_FOUND)
    return AnalyticsResponse(**data).model_dump(mode="json")


@router.get("/{short_code}")
async def get_url(short_code: str, db: Session = Depends(get_db)):
    url = lookup_url(db, short_code)
    if not url:
        return JSONResponse(status_code=404, content=_NOT_FOUND)
    return UrlDetailResponse(
        short_code=url.short_code,
        url=url.original_url,
        created_at=url.created_at,
        expiry_date=url.expiry_date,
        click_count=url.click_count,
    ).model_dump(mode="json")


@router.delete("/{short_code}")
async def delete(short_code: str, db: Session = Depends(get_db)):
    if not delete_url(db, short_code):
        return JSONResponse(status_code=404, content=_NOT_FOUND)
    return Response(status_code=204)
