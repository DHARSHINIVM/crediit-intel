import logging
from typing import List, Optional

from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import schemas, crud, models
from .seed import seed_if_empty
from .scheduler import scheduler

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Real-Time Explainable Credit Intelligence Platform — API",
    version="0.2.0",
)

# Lifespan
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    with next(get_db()) as db:
        seed_if_empty(db)
    scheduler.start()
    logger.info("Application started")

@app.on_event("shutdown")
async def on_shutdown():
    await scheduler.stop()
    logger.info("Shutdown finished")

# Issuer endpoints (same)
@app.get("/issuers", response_model=List[schemas.IssuerRead], summary="List issuers")
def list_issuers(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    return crud.get_issuers(db, skip=skip, limit=limit)

@app.post("/issuers", response_model=schemas.IssuerRead, status_code=201)
def create_issuer(issuer: schemas.IssuerCreate, db: Session = Depends(get_db)):
    return crud.create_issuer(db, issuer)

# Fundamentals endpoints (same)
@app.get("/fundamentals", response_model=List[schemas.FundamentalRead], summary="List fundamentals")
def list_fundamentals(issuer_id: Optional[int] = Query(None), skip: int = Query(0, ge=0),
                      limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    return crud.get_fundamentals(db, skip=skip, limit=limit, issuer_id=issuer_id)

@app.post("/fundamentals", response_model=schemas.FundamentalRead, status_code=201)
def create_fundamental(f: schemas.FundamentalCreate, db: Session = Depends(get_db)):
    issuer = db.query(models.Issuer).filter(models.Issuer.id == f.issuer_id).first()
    if issuer is None:
        raise HTTPException(status_code=400, detail="issuer_id does not exist")
    return crud.create_fundamental(db, f)

# ---- NEWS endpoints ----
@app.get("/news", response_model=List[schemas.NewsRead], summary="List news")
def list_news(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    return crud.get_news(db, skip=skip, limit=limit)

@app.post("/news", response_model=schemas.NewsRead, status_code=201, summary="Create news (manual)")
def create_news(n: schemas.NewsCreate, db: Session = Depends(get_db)):
    # dedupe by link
    if crud.get_news_by_link(db, n.link):
        raise HTTPException(status_code=400, detail="news with same link exists")
    return crud.create_news(db, n)

# ---- EVENTS endpoints ----
@app.get("/events", response_model=List[schemas.EventRead], summary="List events")
def list_events(issuer_id: Optional[int] = Query(None), skip: int = Query(0, ge=0),
                limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    return crud.get_events(db, skip=skip, limit=limit, issuer_id=issuer_id)

@app.post("/events", response_model=schemas.EventRead, status_code=201, summary="Create event (manual)")
def create_event(e: schemas.EventCreate, db: Session = Depends(get_db)):
    return crud.create_event(db, e)

# health
@app.get("/health")
def health():
    return {"status": "ok"}
