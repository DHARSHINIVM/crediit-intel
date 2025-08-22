from sqlalchemy import (
    Column, Integer, String, Date, Float, ForeignKey, DateTime, func, Boolean, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from .database import Base

class Issuer(Base):
    __tablename__ = "issuers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    ticker = Column(String(32), nullable=True, unique=True, index=True)
    country = Column(String(64), nullable=True)

    fundamentals = relationship(
        "Fundamental",
        back_populates="issuer",
        cascade="all, delete-orphan"
    )
    events = relationship("Event", back_populates="issuer")

class Fundamental(Base):
    __tablename__ = "fundamentals"

    id = Column(Integer, primary_key=True, index=True)
    issuer_id = Column(Integer, ForeignKey("issuers.id", ondelete="CASCADE"), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    revenue = Column(Float, nullable=True)
    ebitda = Column(Float, nullable=True)
    total_debt = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    issuer = relationship("Issuer", back_populates="fundamentals")

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(1024), nullable=False)
    link = Column(String(2048), nullable=False, unique=True, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed = Column(Boolean, default=False, nullable=False)  # whether NLP ran on it

    events = relationship("Event", back_populates="news")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    issuer_id = Column(Integer, ForeignKey("issuers.id", ondelete="SET NULL"), nullable=True, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(128), nullable=False, index=True)  # e.g., earnings, merger, price, other
    description = Column(Text, nullable=True)
    sentiment = Column(Float, nullable=True)  # VADER compound score
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    extra = Column(JSON, nullable=True)

    issuer = relationship("Issuer", back_populates="events")
    news = relationship("News", back_populates="events")
