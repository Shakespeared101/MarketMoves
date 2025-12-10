"""
Yahoo Finance Data Ingestion Service
Fetches stock prices, company information, and financial data
"""

import yfinance as yf
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging

from app.config import settings
from app.database.sqlite_manager import db_manager

logger = logging.getLogger(__name__)


class YahooFinanceService:
    """Service for fetching data from Yahoo Finance"""

    def __init__(self):
        self.historical_years = settings.HISTORICAL_DATA_YEARS

    async def fetch_company_info(self, ticker: str) -> Dict[str, Any]:
        """Fetch company information"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            company_data = {
                'ticker': ticker,
                'name': info.get('longName') or info.get('shortName', ticker),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'description': info.get('longBusinessSummary'),
                'website': info.get('website')
            }

            # Store in database
            await db_manager.insert_company(company_data)
            logger.info(f"Fetched company info for {ticker}")

            return company_data

        except Exception as e:
            logger.error(f"Error fetching company info for {ticker}: {e}")
            return None

    async def fetch_historical_prices(
        self,
        ticker: str,
        period: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        Fetch historical stock prices

        Args:
            ticker: Stock ticker symbol
            period: Period to fetch (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        try:
            stock = yf.Ticker(ticker)

            # Fetch historical data
            if period:
                hist = stock.history(period=period)
            elif start_date and end_date:
                hist = stock.history(start=start_date, end=end_date)
            else:
                # Default: last N years
                end = datetime.now()
                start = end - timedelta(days=365 * self.historical_years)
                hist = stock.history(start=start, end=end)

            if hist.empty:
                logger.warning(f"No historical data found for {ticker}")
                return pd.DataFrame()

            # Prepare data for database
            hist.reset_index(inplace=True)
            hist['ticker'] = ticker

            # Rename columns to match database schema
            hist = hist.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            # Add adjusted close if available
            if 'Adj Close' in hist.columns:
                hist = hist.rename(columns={'Adj Close': 'adj_close'})

            # Convert date to string format
            hist['date'] = hist['date'].dt.strftime('%Y-%m-%d')

            # Store in database
            prices_data = hist[['ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']].to_dict('records')
            await db_manager.insert_stock_prices(prices_data)

            logger.info(f"Fetched {len(hist)} price records for {ticker}")

            return hist

        except Exception as e:
            logger.error(f"Error fetching prices for {ticker}: {e}")
            return pd.DataFrame()

    async def fetch_financial_metrics(self, ticker: str) -> Dict[str, Any]:
        """Fetch financial metrics and ratios"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            metrics = {
                'ticker': ticker,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'revenue': info.get('totalRevenue'),
                'net_income': info.get('netIncomeToCommon'),
                'eps': info.get('trailingEps'),
                'pe_ratio': info.get('trailingPE'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'roe': info.get('returnOnEquity'),
                'roa': info.get('returnOnAssets')
            }

            logger.info(f"Fetched financial metrics for {ticker}")
            return metrics

        except Exception as e:
            logger.error(f"Error fetching financial metrics for {ticker}: {e}")
            return None

    async def fetch_latest_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch the latest price and trading info"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            latest = {
                'ticker': ticker,
                'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'change': info.get('regularMarketChange'),
                'change_percent': info.get('regularMarketChangePercent'),
                'volume': info.get('regularMarketVolume'),
                'market_cap': info.get('marketCap'),
                'day_high': info.get('dayHigh'),
                'day_low': info.get('dayLow'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow')
            }

            return latest

        except Exception as e:
            logger.error(f"Error fetching latest price for {ticker}: {e}")
            return None

    async def fetch_multiple_tickers(self, tickers: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple tickers"""
        results = {}

        for ticker in tickers:
            try:
                # Fetch company info
                await self.fetch_company_info(ticker)

                # Fetch historical prices
                prices = await self.fetch_historical_prices(ticker, period=period)
                results[ticker] = prices

                logger.info(f"Successfully fetched data for {ticker}")

            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {e}")
                results[ticker] = pd.DataFrame()

        return results

    async def update_ticker_data(self, ticker: str) -> bool:
        """Update all data for a specific ticker"""
        try:
            # Update company info
            await self.fetch_company_info(ticker)

            # Update prices (last 30 days to catch any gaps)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            await self.fetch_historical_prices(
                ticker,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )

            logger.info(f"Successfully updated data for {ticker}")
            return True

        except Exception as e:
            logger.error(f"Error updating data for {ticker}: {e}")
            return False

    def get_sp500_tickers(self) -> List[str]:
        """Get list of S&P 500 tickers"""
        try:
            # Fetch S&P 500 constituents
            sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
            tickers = sp500['Symbol'].tolist()

            # Clean tickers (replace . with -)
            tickers = [ticker.replace('.', '-') for ticker in tickers]

            logger.info(f"Fetched {len(tickers)} S&P 500 tickers")
            return tickers

        except Exception as e:
            logger.error(f"Error fetching S&P 500 tickers: {e}")
            return []

    def get_popular_tickers(self) -> List[str]:
        """Get a list of popular tickers for demo"""
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
            'META', 'NVDA', 'JPM', 'V', 'WMT',
            'PG', 'JNJ', 'UNH', 'HD', 'DIS',
            'BAC', 'MA', 'XOM', 'PFE', 'CSCO'
        ]

    async def initialize_demo_data(self):
        """Initialize with popular stocks for demo purposes"""
        logger.info("Initializing demo data...")

        tickers = self.get_popular_tickers()[:10]  # Start with 10 stocks

        for ticker in tickers:
            try:
                await self.fetch_company_info(ticker)
                await self.fetch_historical_prices(ticker, period="2y")
                logger.info(f"Initialized data for {ticker}")
            except Exception as e:
                logger.error(f"Error initializing {ticker}: {e}")

        logger.info("Demo data initialization complete")


# Global instance
yahoo_finance = YahooFinanceService()
