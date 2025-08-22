import feedparser
from datetime import datetime, timezone
from dateutil import parser as date_parser
from .nlp import classify_event, analyze_sentiment
from . import crud, models
from sqlalchemy.orm import Session
import logging
import yfinance as yf
import json
from typing import List, Optional
from sqlalchemy import func

logger = logging.getLogger(__name__)

# Configure RSS feeds (example list; add more as needed)
RSS_FEEDS = [
    "https://www.reuters.com/markets/us/rss",    # Reuters markets
    "https://www.ft.com/?format=rss",           # FT (if allowed)
    "https://www.moneycontrol.com/rss/latestnews.xml",
    # Add or replace feeds appropriate to your project (ensure allowed by license)
]

# Ingest RSS news
def ingest_rss(db: Session, feeds: Optional[List[str]] = None) -> int:
    feeds = feeds or RSS_FEEDS
    inserted = 0
    for url in feeds:
        try:
            d = feedparser.parse(url)
            for entry in d.entries:
                link = getattr(entry, "link", None)
                title = getattr(entry, "title", None)
                summary = getattr(entry, "summary", None) or getattr(entry, "description", None, None)
                published = None
                if hasattr(entry, "published"):
                    try:
                        published = date_parser.parse(entry.published)
                        if published.tzinfo is None:
                            published = published.replace(tzinfo=timezone.utc)
                    except Exception:
                        published = None
                # Skip if link or title missing
                if not link or not title:
                    continue
                # dedupe by link
                existing = crud.get_news_by_link(db, link)
                if existing:
                    continue
                n = crud.create_news(db, models.News(
                    title=title.strip(),
                    link=link.strip(),
                    summary=summary,
                    published_at=published
                ))
                inserted += 1
        except Exception as e:
            logger.exception("RSS ingest error for %s: %s", url, e)
    logger.info("RSS ingest completed, inserted=%d", inserted)
    return inserted

# Ingest Yahoo Finance price history for issuers with tickers
def ingest_yahoo_prices(db: Session, period: str = "7d", interval: str = "1d") -> int:
    """
    For each issuer that has a ticker, fetch history and create price events for new rows.
    Stores event with event_type='price' and extra={'close':..,'open':..,'volume':..}
    """
    inserted = 0
    issuers = db.query(models.Issuer).filter(models.Issuer.ticker.isnot(None)).all()
    for issuer in issuers:
        ticker = issuer.ticker.strip()
        if not ticker:
            continue
        try:
            tk = yf.Ticker(ticker)
            hist = tk.history(period=period, interval=interval)
            # DataFrame may be empty
            if hist is None or hist.empty:
                continue
            # iterate rows
            for ts, row in hist.iterrows():
                # ts may be Timestamp; convert to aware datetime (UTC)
                ts_utc = pd_timestamp_to_datetime(ts)
                # check duplicate event for this issuer and timestamp
                exists = db.query(models.Event).filter(
                    models.Event.issuer_id == issuer.id,
                    func.strftime('%Y-%m-%dT%H:%M:%fZ', models.Event.timestamp) == ts_utc.isoformat()
                ).first()
                # Simpler dedupe: check any event with issuer_id and event_type='price' and timestamp within same day
                exists2 = db.query(models.Event).filter(
                    models.Event.issuer_id == issuer.id,
                    models.Event.event_type == 'price',
                    func.date(models.Event.timestamp) == ts_utc.date()
                ).first()
                if exists or exists2:
                    continue
                extra = {
                    "open": float(row.get("Open", None)) if row.get("Open", None) is not None else None,
                    "high": float(row.get("High", None)) if row.get("High", None) is not None else None,
                    "low": float(row.get("Low", None)) if row.get("Low", None) is not None else None,
                    "close": float(row.get("Close", None)) if row.get("Close", None) is not None else None,
                    "volume": int(row.get("Volume", 0)) if row.get("Volume", None) is not None else None,
                }
                # create price event
                e = models.Event(
                    issuer_id=issuer.id,
                    news_id=None,
                    event_type="price",
                    description=f"Price snapshot for {ticker} at {ts_utc.isoformat()}",
                    sentiment=None,
                    timestamp=ts_utc,
                    extra=extra
                )
                db.add(e)
                db.commit()
                db.refresh(e)
                inserted += 1
        except Exception as e:
            logger.exception("Error ingesting prices for %s (%s): %s", issuer.name, issuer.ticker, e)
    logger.info("Yahoo price ingest completed, inserted=%d", inserted)
    return inserted

# small helper to convert pandas Timestamp / datetime-like to timezone-aware datetime in UTC
def pd_timestamp_to_datetime(ts):
    try:
        # If pandas Timestamp, it has tzinfo or tz_localize
        import pandas as pd
        if isinstance(ts, pd.Timestamp):
            if ts.tzinfo is None:
                return ts.to_pydatetime().replace(tzinfo=timezone.utc)
            else:
                return ts.to_pydatetime().astimezone(timezone.utc)
    except Exception:
        pass
    # fallback: assume ts is datetime
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    return datetime.now(timezone.utc)

# Run NLP on unprocessed news, create events
def run_nlp_on_news(db: Session) -> int:
    inserted = 0
    # get unprocessed news rows
    rows = db.query(models.News).filter(models.News.processed == False).order_by(models.News.published_at.desc().nullslast()).all()
    for n in rows:
        text = (n.title or "") + " " + (n.summary or "")
        event_type = classify_event(text)
        sentiment = analyze_sentiment(text)
        # attempt to match issuer by ticker or name present in title
        issuer_id = None
        # find issuer by ticker or name substring
        issuers = db.query(models.Issuer).all()
        title_l = (n.title or "").lower()
        for iss in issuers:
            if iss.ticker and iss.ticker.lower() in title_l:
                issuer_id = iss.id
                break
            if iss.name and iss.name.lower() in title_l:
                issuer_id = iss.id
                break
        # create event linking to the news
        e = models.Event(
            issuer_id=issuer_id,
            news_id=n.id,
            event_type=event_type,
            description=n.summary or n.title,
            sentiment=sentiment,
            timestamp=n.published_at or None,
            extra=None
        )
        db.add(e)
        # mark news processed
        n.processed = True
        db.commit()
        inserted += 1
    logger.info("NLP pass completed, events inserted=%d", inserted)
    return inserted

# top-level ingestion
def ingest_all(db: Session) -> dict:
    """
    Executes RSS ingest, Yahoo price ingest, then runs NLP.
    Returns counts dict for logging/testing.
    """
    inserted_news = ingest_rss(db)
    inserted_prices = ingest_yahoo_prices(db)
    inserted_events = run_nlp_on_news(db)
    return {
        "news": inserted_news,
        "price_events": inserted_prices,
        "nlp_events": inserted_events
    }
