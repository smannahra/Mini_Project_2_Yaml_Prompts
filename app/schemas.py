from datetime import datetime
from pydantic import BaseModel


class ShortenRequest(BaseModel):
    url: str
    expiry_date: datetime | None = None


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    url: str
    created_at: datetime
    expiry_date: datetime | None = None


class UrlDetailResponse(BaseModel):
    short_code: str
    url: str
    created_at: datetime
    expiry_date: datetime | None = None
    click_count: int


class AnalyticsResponse(BaseModel):
    short_code: str
    click_count: int
    last_accessed: datetime | None = None
    referrers: list[str]


class ErrorResponse(BaseModel):
    error: str
    code: str
