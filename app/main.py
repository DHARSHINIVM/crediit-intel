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
    version="0.1.0",
)

# ---- Lifespan Hooks ----
@app.on_event("startup")
def on_startup():
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Seed if empty
    with next(get_db()) as db:
        seed_if_empty(db)
    # Start heartbeat scheduler
    scheduler.start()
    logger.info("Application started")

@app.on_event("shutdown")
async def on_shutdown():
    await scheduler.stop()
    logger.info("Application shutdown complete")

# ---- REST Endpoints ----
@app.get("/issuers", response_model=List[schemas.IssuerRead], summary="List issuers")
def list_issuers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return crud.get_issuers(db, skip=skip, limit=limit)

@app.post("/issuers", response_model=schemas.IssuerRead, status_code=201, summary="Create issuer")
def create_issuer(issuer: schemas.IssuerCreate, db: Session = Depends(get_db)):
    return crud.create_issuer(db, issuer)

@app.get("/fundamentals", response_model=List[schemas.FundamentalRead], summary="List fundamentals")
def list_fundamentals(
    issuer_id: Optional[int] = Query(None, description="Filter by issuer_id"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return crud.get_fundamentals(db, skip=skip, limit=limit, issuer_id=issuer_id)

@app.post("/fundamentals", response_model=schemas.FundamentalRead, status_code=201,
          summary="Create fundamental row")
def create_fundamental(f: schemas.FundamentalCreate, db: Session = Depends(get_db)):
    issuer = db.query(models.Issuer).filter(models.Issuer.id == f.issuer_id).first()
    if issuer is None:
        raise HTTPException(status_code=400, detail="issuer_id does not exist")
    return crud.create_fundamental(db, f)

@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}
