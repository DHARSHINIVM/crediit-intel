from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List

# ---- Issuer ----
class IssuerBase(BaseModel):
    name: str = Field(..., examples=["Acme Corp"])
    ticker: Optional[str] = Field(None, examples=["ACME"])
    country: Optional[str] = Field(None, examples=["IN"])

class IssuerCreate(IssuerBase):
    pass

class IssuerRead(IssuerBase):
    id: int
    class Config:
        from_attributes = True

# ---- Fundamental ----
class FundamentalBase(BaseModel):
    issuer_id: int
    report_date: date
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    total_debt: Optional[float] = None

class FundamentalCreate(FundamentalBase):
    pass

class FundamentalRead(FundamentalBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Optional nested type for future use
class IssuerWithFundamentals(IssuerRead):
    fundamentals: List[FundamentalRead] = []
