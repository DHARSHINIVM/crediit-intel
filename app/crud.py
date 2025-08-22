from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas
from datetime import datetime

# ---- Issuers & Fundamentals (same as Day1) ----
def get_issuers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Issuer]:
    return db.query(models.Issuer).offset(skip).limit(limit).all()

def create_issuer(db: Session, issuer: schemas.IssuerCreate) -> models.Issuer:
    db_obj = models.Issuer(**issuer.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

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

# ---- NEWS ----
def get_news(db: Session, skip: int = 0, limit: int = 100) -> List[models.News]:
    return db.query(models.News).order_by(models.News.published_at.desc().nullslast()).offset(skip).limit(limit).all()

def get_news_by_link(db: Session, link: str) -> Optional[models.News]:
    return db.query(models.News).filter(models.News.link == link).first()

def create_news(db: Session, news: schemas.NewsCreate) -> models.News:
    db_obj = models.News(**news.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# ---- EVENTS ----
def get_events(db: Session, skip: int = 0, limit: int = 100, issuer_id: Optional[int] = None):
    q = db.query(models.Event)
    if issuer_id is not None:
        q = q.filter(models.Event.issuer_id == issuer_id)
    return q.order_by(models.Event.timestamp.desc()).offset(skip).limit(limit).all()

def create_event(db: Session, e: schemas.EventCreate) -> models.Event:
    payload = e.model_dump()
    # if timestamp is None, SQL default applies
    db_obj = models.Event(**payload)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
