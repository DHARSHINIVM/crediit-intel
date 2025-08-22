from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas

# ---- Issuers ----
def get_issuers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Issuer]:
    return db.query(models.Issuer).offset(skip).limit(limit).all()

def create_issuer(db: Session, issuer: schemas.IssuerCreate) -> models.Issuer:
    db_obj = models.Issuer(**issuer.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# ---- Fundamentals ----
def get_fundamentals(db: Session, skip: int = 0, limit: int = 100, issuer_id: Optional[int] = None):
    q = db.query(models.Fundamental)
    if issuer_id is not None:
        q = q.filter(models.Fundamental.issuer_id == issuer_id)
    return q.order_by(models.Fundamental.report_date.desc()).offset(skip).limit(limit).all()

def create_fundamental(db: Session, fundamental: schemas.FundamentalCreate) -> models.Fundamental:
    db_obj = models.Fundamental(**fundamental.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
