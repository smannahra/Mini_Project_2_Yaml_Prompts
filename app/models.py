from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Url(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    short_code: Mapped[str] = mapped_column(String(6), unique=True, nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    click_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    click_events: Mapped[list["ClickEvent"]] = relationship(
        "ClickEvent", back_populates="url", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_urls_short_code", "short_code"),
        Index("ix_urls_original_url", "original_url"),
    )

    def __repr__(self) -> str:
        return f"<Url short_code={self.short_code!r} url={self.original_url!r}>"


class ClickEvent(Base):
    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("urls.id", ondelete="CASCADE"), nullable=False
    )
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    url: Mapped["Url"] = relationship("Url", back_populates="click_events")

    def __repr__(self) -> str:
        return f"<ClickEvent url_id={self.url_id} referrer={self.referrer!r}>"
