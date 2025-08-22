from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
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
