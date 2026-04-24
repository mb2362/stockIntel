"""News endpoint — newsdata.io + VADER sentiment analysis."""
import os
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

router = APIRouter()
analyzer = SentimentIntensityAnalyzer()

NEWSDATA_API_KEY = os.environ.get("NEWSDATA_API_KEY", "pub_dfb396622a514546b24b057496157fcd")
NEWSDATA_URL = "https://newsdata.io/api/1/news"

RANGE_DAYS = {"1D": 1, "1W": 7, "1M": 30}
RANGE_FMT  = {"1D": "%H:00", "1W": "%b %d", "1M": "%b %d"}


def _classify(score: float) -> str:
    if score >= 0.05:  return "positive"
    if score <= -0.05: return "negative"
    return "neutral"


def _score_text(title: str, description: str | None) -> float:
    return analyzer.polarity_scores(f"{title}. {description or ''}")["compound"]


def _bucket(pub_date: str, range: str) -> str:
    try:
        dt = datetime.strptime(pub_date[:19], "%Y-%m-%d %H:%M:%S")
        return dt.strftime(RANGE_FMT[range])
    except Exception:
        return "Unknown"


@router.get("/news")
async def get_news(
    ticker: str = Query("AAPL"),
    range:  str = Query("1W"),
):
    ticker = ticker.upper()
    range  = range.upper()

    if range not in RANGE_DAYS:
        range = "1W"

    if not NEWSDATA_API_KEY:
        raise HTTPException(status_code=500, detail="NEWSDATA_API_KEY not configured")

    params = {
        "apikey":    NEWSDATA_API_KEY,
        "q":         ticker,
        "language":  "en",
        "category":  "business",
        "size":      10,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(NEWSDATA_URL, params=params)

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch news")

    results = resp.json().get("results", [])

    news_items = []
    daily_scores: dict[str, list[float]] = {}

    for item in results:
        title       = item.get("title") or ""
        description = item.get("description") or ""
        pub_date    = item.get("pubDate") or ""

        score     = _score_text(title, description)
        sentiment = _classify(score)
        bucket    = _bucket(pub_date, range)

        daily_scores.setdefault(bucket, []).append(score)

        news_items.append({
            "title":       title,
            "description": description,
            "url":         item.get("link") or "#",
            "source":      item.get("source_id") or "Unknown",
            "publishedAt": pub_date,
            "sentiment":   sentiment,
            "score":       round(score, 4),
        })

    trend = [
        {"date": day, "sentimentScore": round(sum(s) / len(s), 4)}
        for day, s in daily_scores.items()
    ]

    return {"ticker": ticker, "range": range, "news": news_items, "trend": trend}