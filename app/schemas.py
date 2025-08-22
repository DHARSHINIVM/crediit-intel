from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Any

# Issuer & Fundamental (same as Day 1)
class IssuerBase(BaseModel):
    name: str
    ticker: Optional[str] = None
    country: Optional[str] = None

class IssuerCreate(IssuerBase): pass

class IssuerRead(IssuerBase):
    id: int
    class Config:
        from_attributes = True

class FundamentalBase(BaseModel):
    issuer_id: int
    report_date: date
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    total_debt: Optional[float] = None

class FundamentalCreate(FundamentalBase): pass

class FundamentalRead(FundamentalBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ---- NEWS ----
class NewsBase(BaseModel):
    title: str
    link: str
    published_at: Optional[datetime] = None
    summary: Optional[str] = None

class NewsCreate(NewsBase): pass

class NewsRead(NewsBase):
    id: int
    created_at: datetime
    processed: bool
    class Config:
        from_attributes = True

# ---- EVENT ----
class EventBase(BaseModel):
    issuer_id: Optional[int] = None
    news_id: Optional[int] = None
    event_type: str
    description: Optional[str] = None
    sentiment: Optional[float] = None
    timestamp: Optional[datetime] = None
    extra: Optional[Any] = None

class EventCreate(EventBase): pass

class EventRead(EventBase):
    id: int
    class Config:
        from_attributes = True
