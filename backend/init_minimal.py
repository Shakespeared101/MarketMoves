"""
Quick Minimal Initialization - Just 2 companies to avoid rate limits
"""

import asyncio
import sys
import logging

sys.path.insert(0, '.')

from app.database.sqlite_manager import db_manager
from app.services.data_ingestion.yahoo_finance import yahoo_finance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize_minimal():
    """Initialize with just 2 companies to avoid rate limits"""

    logger.info("=" * 60)
    logger.info("MarketMoves Minimal Initialization (2 companies)")
    logger.info("=" * 60)

    # Initialize database
    logger.info("\n[1/2] Initializing database...")
    await db_manager.init_database()
    logger.info("✓ Database ready")

    # Fetch just 2 companies
    logger.info("\n[2/2] Fetching data for 2 companies...")
    tickers = ['AAPL', 'MSFT']

    for i, ticker in enumerate(tickers, 1):
        try:
            logger.info(f"\n[{i}/2] Fetching {ticker}...")

            # Fetch company info
            await yahoo_finance.fetch_company_info(ticker)

            # Fetch 1 year of data (faster than 2y)
            await yahoo_finance.fetch_historical_prices(ticker, period='1y')

            logger.info(f"✓ {ticker} complete")

            # Wait between requests
            if i < len(tickers):
                logger.info("Waiting 10 seconds...")
                await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"✗ Error fetching {ticker}: {e}")

    # Summary
    companies = await db_manager.get_all_companies()
    logger.info(f"\n✓ Loaded {len(companies)} companies")

    logger.info("\n" + "=" * 60)
    logger.info("Ready to start!")
    logger.info("=" * 60)
    logger.info("\nRun: python -m app.main")
    logger.info("\n")


if __name__ == "__main__":
    try:
        asyncio.run(initialize_minimal())
    except KeyboardInterrupt:
        logger.info("\nCancelled")
    except Exception as e:
        logger.error(f"\nError: {e}")
        sys.exit(1)
