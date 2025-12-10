"""
Create sample data for immediate testing
No API calls - just creates mock data in the database
"""

import asyncio
import sys
from datetime import datetime, timedelta
import random

sys.path.insert(0, '.')

from app.database.sqlite_manager import db_manager

print("Creating sample data for MarketMoves...")

async def create_sample_data():
    """Create sample companies and stock data"""

    # Initialize database
    await db_manager.init_database()
    print("✓ Database initialized")

    # Sample companies
    companies = [
        {'ticker': 'AAPL', 'name': 'Apple Inc.', 'sector': 'Technology', 'industry': 'Consumer Electronics', 'market_cap': 3000000000000},
        {'ticker': 'MSFT', 'name': 'Microsoft Corporation', 'sector': 'Technology', 'industry': 'Software', 'market_cap': 2800000000000},
        {'ticker': 'GOOGL', 'name': 'Alphabet Inc.', 'sector': 'Technology', 'industry': 'Internet', 'market_cap': 1800000000000},
        {'ticker': 'AMZN', 'name': 'Amazon.com Inc.', 'sector': 'Consumer Cyclical', 'industry': 'E-Commerce', 'market_cap': 1500000000000},
        {'ticker': 'TSLA', 'name': 'Tesla Inc.', 'sector': 'Automotive', 'industry': 'Electric Vehicles', 'market_cap': 800000000000},
    ]

    print("\nAdding companies...")
    for company in companies:
        await db_manager.insert_company(company)
        print(f"  ✓ {company['ticker']} - {company['name']}")

    # Generate sample price data
    print("\nGenerating sample price data...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    for company in companies:
        ticker = company['ticker']
        base_price = random.uniform(100, 300)

        prices_data = []
        current_date = start_date
        current_price = base_price

        while current_date <= end_date:
            # Random walk price
            change = random.uniform(-0.03, 0.03)  # ±3% daily change
            current_price *= (1 + change)

            prices_data.append({
                'ticker': ticker,
                'date': current_date.strftime('%Y-%m-%d'),
                'open': current_price * random.uniform(0.99, 1.01),
                'high': current_price * random.uniform(1.00, 1.02),
                'low': current_price * random.uniform(0.98, 1.00),
                'close': current_price,
                'volume': random.randint(10000000, 100000000),
                'adj_close': current_price
            })

            current_date += timedelta(days=1)

        await db_manager.insert_stock_prices(prices_data)
        print(f"  ✓ {ticker}: {len(prices_data)} price records")

    # Add sample news
    print("\nAdding sample news articles...")
    news_items = [
        {
            'ticker': 'AAPL',
            'headline': 'Apple Announces New iPhone with AI Features',
            'summary': 'Latest iPhone includes advanced AI capabilities',
            'source': 'Tech News',
            'published_date': (datetime.now() - timedelta(days=2)).isoformat(),
            'sentiment_score': 0.6,
            'sentiment_label': 'positive'
        },
        {
            'ticker': 'MSFT',
            'headline': 'Microsoft Azure Revenue Grows 30%',
            'summary': 'Cloud services continue strong growth',
            'source': 'Financial Times',
            'published_date': (datetime.now() - timedelta(days=5)).isoformat(),
            'sentiment_score': 0.7,
            'sentiment_label': 'positive'
        },
        {
            'ticker': 'TSLA',
            'headline': 'Tesla Faces Production Delays',
            'summary': 'Supply chain issues affect manufacturing',
            'source': 'Reuters',
            'published_date': (datetime.now() - timedelta(days=1)).isoformat(),
            'sentiment_score': -0.4,
            'sentiment_label': 'negative'
        },
    ]

    for news in news_items:
        await db_manager.insert_news_article(news)
        print(f"  ✓ {news['ticker']}: {news['headline']}")

    # Add sample risk scores
    print("\nAdding sample risk scores...")
    for company in companies:
        ticker = company['ticker']

        # Generate risk scores for last 90 days
        current_date = datetime.now() - timedelta(days=90)

        while current_date <= datetime.now():
            risk_score = random.uniform(2.0, 7.0)

            await db_manager.insert_risk_score({
                'ticker': ticker,
                'date': current_date.strftime('%Y-%m-%d'),
                'overall_risk_score': risk_score,
                'volatility_score': risk_score * random.uniform(0.8, 1.2),
                'litigation_score': random.uniform(1.0, 5.0),
                'sentiment_score': random.uniform(2.0, 6.0),
                'financial_anomaly_score': random.uniform(1.0, 4.0),
                'regulatory_score': random.uniform(1.0, 3.0),
                'risk_level': 'Medium' if risk_score < 6 else 'High'
            })

            current_date += timedelta(days=7)  # Weekly

        print(f"  ✓ {ticker}: Risk timeline created")

    print("\n" + "=" * 60)
    print("✓ Sample data created successfully!")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. Start backend: python -m app.main")
    print("  2. Start frontend: cd ../frontend && npm run dev")
    print("  3. Open http://localhost:5173")
    print("\n")

if __name__ == "__main__":
    try:
        asyncio.run(create_sample_data())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
