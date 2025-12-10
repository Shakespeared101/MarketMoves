"""Market Data API Routes"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.database.sqlite_manager import db_manager
from app.services.data_ingestion.yahoo_finance import yahoo_finance

router = APIRouter()


@router.get("/companies")
async def get_companies():
    """Get all tracked companies"""
    companies = await db_manager.get_all_companies()
    return {"companies": companies, "count": len(companies)}


@router.get("/companies/{ticker}")
async def get_company(ticker: str):
    """Get company details"""
    company = await db_manager.get_company(ticker)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/stocks/{ticker}/prices")
async def get_stock_prices(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get stock prices for a ticker"""
    prices = await db_manager.get_stock_prices(ticker, start_date, end_date)
    return {"ticker": ticker, "prices": prices[:limit], "count": len(prices)}


@router.get("/stocks/{ticker}/latest")
async def get_latest_price(ticker: str):
    """Get latest price and trading info from database"""
    # Get the most recent price from database
    prices = await db_manager.get_stock_prices(ticker, limit=2)

    if not prices or len(prices) == 0:
        raise HTTPException(status_code=404, detail="Price data not found")

    latest = prices[0]
    previous = prices[1] if len(prices) > 1 else None

    # Calculate change
    change = 0
    change_percent = 0
    if previous:
        change = latest['close'] - previous['close']
        change_percent = (change / previous['close']) * 100

    return {
        "ticker": ticker,
        "price": latest['close'],
        "change": change,
        "change_percent": change_percent,
        "volume": latest['volume'],
        "date": latest['date'],
        "day_high": latest['high'],
        "day_low": latest['low']
    }


@router.post("/stocks/{ticker}/update")
async def update_ticker_data(ticker: str):
    """Update data for a ticker"""
    success = await yahoo_finance.update_ticker_data(ticker)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update data")
    return {"message": f"Successfully updated data for {ticker}"}
