"""
Initialize Demo Data for MarketMoves
Fetches sample stock data using Alpha Vantage and NewsAPI
Populates Neo4j with entity relationships
"""

import asyncio
import sys
import logging

# Add parent directory to path
sys.path.insert(0, '.')

from app.database.sqlite_manager import db_manager
from app.database.neo4j_manager import neo4j_manager
from app.database.duckdb_analytics import analytics
from app.services.data_ingestion.alpha_vantage_service import alpha_vantage_service
from app.services.data_ingestion.legal_data_service import legal_data_service
from app.services.risk_engine import risk_engine
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize():
    """Initialize database and load demo data"""

    logger.info("=" * 60)
    logger.info("MarketMoves Demo Data Initialization")
    logger.info("=" * 60)

    # Step 1: Initialize databases
    logger.info("\n[1/6] Initializing database schemas...")
    await db_manager.init_database()
    logger.info("✓ SQLite schema created")

    # Initialize Neo4j
    try:
        await neo4j_manager.connect()
        logger.info("✓ Neo4j connected")
    except Exception as e:
        logger.warning(f"⚠ Neo4j connection failed: {e}")
        logger.warning("  Continuing without Neo4j (graph features will be unavailable)")

    # Step 2: Fetch company information
    logger.info("\n[2/6] Fetching company information...")

    popular_tickers = [
        'AAPL',  # Apple
        'MSFT',  # Microsoft
        'GOOGL', # Google
        'AMZN',  # Amazon
        'TSLA',  # Tesla
    ]

    companies_loaded = []

    for ticker in popular_tickers:
        try:
            logger.info(f"  Fetching {ticker}...")

            # Fetch company info
            company_data = await alpha_vantage_service.fetch_company_info(ticker)

            if company_data:
                companies_loaded.append(ticker)
                logger.info(f"  ✓ {ticker} company info fetched")

                # Store in Neo4j
                if neo4j_manager.driver:
                    try:
                        await legal_data_service.store_legal_data_in_neo4j(
                            ticker,
                            company_data['name'],
                            company_data
                        )
                        logger.info(f"  ✓ {ticker} entity graph created in Neo4j")
                    except Exception as e:
                        logger.warning(f"  ⚠ Neo4j error for {ticker}: {e}")

            # Rate limiting - Alpha Vantage free tier: 5 requests/minute
            if settings.ALPHA_VANTAGE_KEY and settings.ALPHA_VANTAGE_KEY != "your_alphavantage_key_here":
                logger.info("  Waiting 12 seconds to avoid API rate limits...")
                await asyncio.sleep(12)

        except Exception as e:
            logger.error(f"  ✗ Failed to fetch {ticker}: {e}")

    logger.info(f"✓ Company information loaded for {len(companies_loaded)} companies")

    # Step 3: Fetch historical prices (sample for first 3 companies)
    logger.info("\n[3/6] Fetching historical stock prices (limited sample)...")

    for ticker in companies_loaded[:3]:  # Only fetch prices for first 3 to save API calls
        try:
            logger.info(f"  Fetching prices for {ticker}...")

            # Fetch prices (compact = last 100 days)
            prices = await alpha_vantage_service.fetch_historical_prices(ticker, outputsize='compact')

            if prices:
                logger.info(f"  ✓ {ticker}: {len(prices)} price records")
            else:
                logger.warning(f"  ⚠ No price data for {ticker}")

            # Rate limiting
            if settings.ALPHA_VANTAGE_KEY and settings.ALPHA_VANTAGE_KEY != "your_alphavantage_key_here":
                logger.info("  Waiting 12 seconds to avoid API rate limits...")
                await asyncio.sleep(12)

        except Exception as e:
            logger.error(f"  ✗ Failed to fetch prices for {ticker}: {e}")

    logger.info("✓ Stock price data loaded")

    # Step 4: Sync data to DuckDB for analytics
    logger.info("\n[4/6] Syncing data to DuckDB for analytics...")
    try:
        analytics.load_from_sqlite(settings.SQLITE_DB_PATH)
        logger.info("✓ Data synced to DuckDB")
    except Exception as e:
        logger.warning(f"⚠ DuckDB sync warning: {e}")

    # Step 5: Calculate risk scores
    logger.info("\n[5/6] Calculating risk scores...")

    for ticker in companies_loaded[:5]:  # Calculate for first 5 companies
        try:
            logger.info(f"  Calculating risk for {ticker}...")
            risk_data = await risk_engine.calculate_overall_risk(ticker)

            if risk_data:
                logger.info(
                    f"  ✓ {ticker}: Risk Score = {risk_data['overall_risk_score']:.1f} "
                    f"({risk_data['risk_level']})"
                )
        except Exception as e:
            logger.warning(f"  ⚠ Failed to calculate risk for {ticker}: {e}")

    logger.info("✓ Risk score calculation complete")

    # Step 6: Summary
    logger.info("\n[6/6] Initialization Summary")
    companies = await db_manager.get_all_companies()
    logger.info(f"  Total companies loaded: {len(companies)}")

    if neo4j_manager.driver:
        logger.info(f"  Neo4j graph database: Active")
        logger.info(f"  Entity relationships: Created for {len(companies_loaded)} companies")
    else:
        logger.info(f"  Neo4j graph database: Unavailable")

    logger.info("\n" + "=" * 60)
    logger.info("✓ Demo data initialization complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("  1. Start Neo4j (if not running): docker-compose up neo4j -d")
    logger.info("  2. Start the backend: python -m app.main")
    logger.info("  3. Start the frontend: cd frontend && npm run dev")
    logger.info("  4. Access the dashboard: http://localhost:5173")
    logger.info("\nNote: For full data, configure API keys in .env:")
    logger.info("  - ALPHA_VANTAGE_KEY (for stock prices)")
    logger.info("  - NEWSAPI_KEY (for news articles)")
    logger.info("\n")


if __name__ == "__main__":
    try:
        asyncio.run(initialize())
    except KeyboardInterrupt:
        logger.info("\n\nInitialization cancelled by user")
    except Exception as e:
        logger.error(f"\n\nError during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
