from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Tuple
import re

analyzer = SentimentIntensityAnalyzer()

# Very simple keyword-based event classification
KEYWORDS = {
    "earnings": ["earnings", "q1", "q2", "q3", "q4", "quarter", "results", "profit"],
    "merger": ["merger", "acquire", "acquisition", "buyout", "takeover"],
    "downgrade": ["downgrade", "cut rating", "lowered", "revised down"],
    "upgrade": ["upgrade", "raised", "reiterat", "upgraded"],
    "lawsuit": ["lawsuit", "sued", "legal", "settlement", "lawsuits"],
    "management": ["ceo", "cfo", "resign", "appoint", "appoints", "board"],
    # fallback: price-related events will be created by price ingestion
}

def classify_event(text: str) -> str:
    t = (text or "").lower()
    # quick tokenization
    for etype, kws in KEYWORDS.items():
        for kw in kws:
            if kw in t:
                return etype
    return "other"

def analyze_sentiment(text: str) -> float:
    if not text:
        return 0.0
    vs = analyzer.polarity_scores(text)
    # return compound score between -1..1
    return float(vs.get("compound", 0.0))
