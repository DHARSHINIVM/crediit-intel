"""
Feature engineering utilities.

We compute a small set of features for each issuer using recent fundamentals
and recent NLP sentiment events:
- debt_to_ebitda: total_debt / max(ebitda, eps)
- ebitda_margin: ebitda / max(revenue, eps)
- revenue_growth: (latest_revenue - prev_revenue) / max(prev_revenue, eps)
- avg_sentiment: average sentiment from events associated with issuer (last N)
- recent_revenue: latest revenue (raw)
- recent_total_debt: latest total_debt (raw)
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import math
from . import models

EPS = 1e-6

def _safe_div(a: Optional[float], b: Optional[float]) -> float:
    try:
        if a is None or b is None:
            return 0.0
        return float(a) / (float(b) if abs(float(b)) > EPS else EPS)
    except Exception:
        return 0.0

def compute_features_for_issuer(db: Session, issuer_id: int) -> Dict[str, Any]:
    """
    Compute features for the given issuer_id using the latest two fundamentals and recent events.
    Returns feature dict in deterministic order.
    """
    # fetch fundamentals ordered by report_date desc
    f_rows = db.query(models.Fundamental).filter(models.Fundamental.issuer_id == issuer_id).order_by(models.Fundamental.report_date.desc()).limit(5).all()
    if not f_rows:
        # return a default zeroed feature vector
        return {
            "debt_to_ebitda": 0.0,
            "ebitda_margin": 0.0,
            "revenue_growth": 0.0,
            "avg_sentiment": 0.0,
            "recent_revenue": 0.0,
            "recent_total_debt": 0.0,
        }

    latest = f_rows[0]
    prev = f_rows[1] if len(f_rows) > 1 else None

    # debt_to_ebitda
    debt = latest.total_debt or 0.0
    ebitda = latest.ebitda or 0.0
    debt_to_ebitda = _safe_div(debt, ebitda)

    # ebitda_margin
    revenue = latest.revenue or 0.0
    ebitda_margin = _safe_div(ebitda, revenue)

    # revenue_growth (relative)
    if prev:
        prev_revenue = prev.revenue or 0.0
        revenue_growth = _safe_div(revenue - prev_revenue, prev_revenue if abs(prev_revenue) > EPS else EPS)
    else:
        revenue_growth = 0.0

    # sentiment: average of last N events for this issuer (or linked news)
    events = db.query(models.Event).filter(models.Event.issuer_id == issuer_id).order_by(models.Event.timestamp.desc()).limit(10).all()
    sentiments = [e.sentiment for e in events if e.sentiment is not None]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

    feats = {
        "debt_to_ebitda": float(debt_to_ebitda),
        "ebitda_margin": float(ebitda_margin),
        "revenue_growth": float(revenue_growth),
        "avg_sentiment": float(avg_sentiment),
        "recent_revenue": float(revenue),
        "recent_total_debt": float(debt),
    }
    return feats
