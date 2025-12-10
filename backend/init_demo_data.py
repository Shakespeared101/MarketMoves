"""
Initialize Demo Data for MarketMoves
Fetches sample stock data for popular companies
"""

import asyncio
import sys
import logging

# Add parent directory to path
sys.path.insert(0, '.')

from app.database.sqlite_manager import db_manager
from app.services.data_ingestion.yahoo_finance import yahoo_finance
from app.services.risk_engine import risk_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize():
    """Initialize database and load demo data"""

    logger.info("=" * 60)
    logger.info("MarketMoves Demo Data Initialization")
    logger.info("=" * 60)

    # Step 1: Initialize database
    logger.info("\n[1/4] Initializing database schema...")
    await db_manager.init_database()
    logger.info("✓ Database schema created")

    # Step 2: Fetch stock data
    logger.info("\n[2/4] Fetching stock data for popular companies...")
    logger.info("This may take a few minutes...")

    popular_tickers = [
        'AAPL',  # Apple
        'MSFT',  # Microsoft
        'GOOGL', # Google
        'AMZN',  # Amazon
        'TSLA',  # Tesla
        'META',  # Meta (Facebook)
        'NVDA',  # NVIDIA
        'JPM',   # JPMorgan Chase
        'V',     # Visa
        'WMT',   # Walmart
    ]

    for ticker in popular_tickers:
        try:
            logger.info(f"  Fetching {ticker}...")

            # Fetch company info
            await yahoo_finance.fetch_company_info(ticker)

            # Fetch 2 years of historical data
            await yahoo_finance.fetch_historical_prices(ticker, period='2y')

            logger.info(f"  ✓ {ticker} completed")

            # Add delay to avoid rate limiting (Yahoo Finance limits)
            logger.info("  Waiting 5 seconds to avoid rate limits...")
            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"  ✗ Failed to fetch {ticker}: {e}")

    logger.info("✓ Stock data fetching complete")

    # Step 3: Calculate initial risk scores
    logger.info("\n[3/4] Calculating risk scores...")

    for ticker in popular_tickers[:5]:  # Calculate for first 5 companies
        try:
            logger.info(f"  Calculating risk for {ticker}...")
            risk_data = await risk_engine.calculate_overall_risk(ticker)
            logger.info(f"  ✓ {ticker}: Risk Score = {risk_data['overall_risk_score']:.1f} ({risk_data['risk_level']})")
        except Exception as e:
            logger.error(f"  ✗ Failed to calculate risk for {ticker}: {e}")

    logger.info("✓ Risk score calculation complete")

    # Step 4: Summary
    logger.info("\n[4/4] Initialization Summary")
    companies = await db_manager.get_all_companies()
    logger.info(f"  Total companies loaded: {len(companies)}")

    logger.info("\n" + "=" * 60)
    logger.info("✓ Demo data initialization complete!")
    logger.info("=" * 60)
    logger.info("\nYou can now:")
    logger.info("  1. Start the backend: python -m app.main")
    logger.info("  2. Start the frontend: cd ../frontend && npm run dev")
    logger.info("  3. Access the dashboard: http://localhost:5173")
    logger.info("\n")


if __name__ == "__main__":
    try:
        asyncio.run(initialize())
    except KeyboardInterrupt:
        logger.info("\n\nInitialization cancelled by user")
    except Exception as e:
        logger.error(f"\n\nError during initialization: {e}")
        sys.exit(1)
