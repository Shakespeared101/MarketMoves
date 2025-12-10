"""
Alpha Vantage Data Service for MarketMoves
Free alternative to Yahoo Finance for stock data
"""

import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio

from app.config import settings
from app.database.sqlite_manager import db_manager

logger = logging.getLogger(__name__)


class AlphaVantageService:
    """Service for fetching stock data from Alpha Vantage API"""

    def __init__(self):
        self.api_key = settings.ALPHA_VANTAGE_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12  # Free tier: 5 requests/minute

    async def fetch_company_info(self, ticker: str) -> Dict[str, Any]:
        """Fetch company overview information"""
        if not self.api_key or self.api_key == "your_alphavantage_key_here":
            logger.warning(f"Alpha Vantage key not configured for {ticker}")
            return await self._get_fallback_company_info(ticker)

        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': ticker,
                'apikey': self.api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'Symbol' not in data:
                            logger.warning(f"No data returned for {ticker}, using fallback")
                            return await self._get_fallback_company_info(ticker)

                        company_data = {
                            'ticker': ticker,
                            'name': data.get('Name', ticker),
                            'sector': data.get('Sector'),
                            'industry': data.get('Industry'),
                            'market_cap': self._parse_number(data.get('MarketCapitalization')),
                            'description': data.get('Description'),
                            'website': data.get('OfficialSite')
                        }

                        await db_manager.insert_company(company_data)
                        logger.info(f"Fetched company info for {ticker}")
                        return company_data

                    else:
                        logger.error(f"Alpha Vantage error: {response.status}")
                        return await self._get_fallback_company_info(ticker)

        except Exception as e:
            logger.error(f"Error fetching company info for {ticker}: {e}")
            return await self._get_fallback_company_info(ticker)

    async def fetch_historical_prices(self, ticker: str, outputsize: str = 'full') -> List[Dict[str, Any]]:
        """
        Fetch historical daily stock prices
        outputsize: 'compact' (100 days) or 'full' (20+ years)
        """
        if not self.api_key or self.api_key == "your_alphavantage_key_here":
            logger.warning(f"Alpha Vantage key not configured for {ticker}")
            return []

        try:
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': ticker,
                'outputsize': outputsize,
                'apikey': self.api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'Time Series (Daily)' not in data:
                            logger.warning(f"No price data for {ticker}")
                            return []

                        time_series = data['Time Series (Daily)']

                        # Convert to our format
                        prices = []
                        for date_str, values in time_series.items():
                            prices.append({
                                'ticker': ticker,
                                'date': date_str,
                                'open': float(values['1. open']),
                                'high': float(values['2. high']),
                                'low': float(values['3. low']),
                                'close': float(values['4. close']),
                                'volume': int(values['6. volume']),
                                'adj_close': float(values['5. adjusted close'])
                            })

                        # Store in database
                        if prices:
                            await db_manager.insert_stock_prices(prices)
                            logger.info(f"Fetched {len(prices)} price records for {ticker}")

                        return prices

                    else:
                        logger.error(f"Alpha Vantage error: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error fetching prices for {ticker}: {e}")
            return []

    def _parse_number(self, value: str) -> Optional[float]:
        """Parse number string to float"""
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def _get_fallback_company_info(self, ticker: str) -> Dict[str, Any]:
        """Fallback company data when API is unavailable"""
        # Basic fallback data for common tickers
        fallback_data = {
            'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'industry': 'Consumer Electronics'},
            'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology', 'industry': 'Software'},
            'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology', 'industry': 'Internet'},
            'AMZN': {'name': 'Amazon.com, Inc.', 'sector': 'Consumer Cyclical', 'industry': 'Internet Retail'},
            'TSLA': {'name': 'Tesla, Inc.', 'sector': 'Consumer Cyclical', 'industry': 'Auto Manufacturers'},
            'META': {'name': 'Meta Platforms, Inc.', 'sector': 'Technology', 'industry': 'Internet'},
            'NVDA': {'name': 'NVIDIA Corporation', 'sector': 'Technology', 'industry': 'Semiconductors'},
            'JPM': {'name': 'JPMorgan Chase & Co.', 'sector': 'Financial Services', 'industry': 'Banks'},
            'V': {'name': 'Visa Inc.', 'sector': 'Financial Services', 'industry': 'Credit Services'},
            'WMT': {'name': 'Walmart Inc.', 'sector': 'Consumer Defensive', 'industry': 'Discount Stores'}
        }

        if ticker in fallback_data:
            company_data = {
                'ticker': ticker,
                **fallback_data[ticker],
                'market_cap': None,
                'description': f"{fallback_data[ticker]['name']} - A leading company in {fallback_data[ticker]['industry']}",
                'website': None
            }
            await db_manager.insert_company(company_data)
            return company_data

        # Generic fallback
        company_data = {
            'ticker': ticker,
            'name': ticker,
            'sector': None,
            'industry': None,
            'market_cap': None,
            'description': None,
            'website': None
        }
        await db_manager.insert_company(company_data)
        return company_data


# Global instance
alpha_vantage_service = AlphaVantageService()
