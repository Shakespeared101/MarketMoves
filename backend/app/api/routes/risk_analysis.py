"""Risk Analysis API Routes"""

from fastapi import APIRouter, HTTPException
from typing import List

from app.services.risk_engine import risk_engine

router = APIRouter()


@router.get("/{ticker}")
async def get_risk_score(ticker: str):
    """Get current risk score for a ticker"""
    risk_data = await risk_engine.calculate_overall_risk(ticker)
    return risk_data


@router.get("/{ticker}/timeline")
async def get_risk_timeline(ticker: str, days: int = 90):
    """Get risk score timeline"""
    timeline = await risk_engine.get_risk_timeline(ticker, days=days)
    return {"ticker": ticker, "timeline": timeline}


@router.post("/calculate")
async def calculate_risk_batch(tickers: List[str]):
    """Calculate risk for multiple tickers"""
    results = await risk_engine.calculate_risk_for_multiple_tickers(tickers)
    return results
