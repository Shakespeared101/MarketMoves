"""
SQLite Database Manager for MarketMoves
Handles all CRUD operations and schema management
"""

import sqlite3
import aiosqlite
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class SQLiteManager:
    """Manages SQLite database operations"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init_database(self):
        """Initialize database with schema"""
        async with aiosqlite.connect(self.db_path) as db:
            await self._create_tables(db)
            await db.commit()
        logger.info(f"Database initialized at {self.db_path}")

    async def _create_tables(self, db: aiosqlite.Connection):
        """Create all database tables"""

        # Companies table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR(10) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                sector VARCHAR(100),
                industry VARCHAR(100),
                market_cap REAL,
                description TEXT,
                website VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Stock prices table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume BIGINT,
                adj_close REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, date),
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            )
        """)

        # SEC filings table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sec_filings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR(10) NOT NULL,
                filing_type VARCHAR(20) NOT NULL,
                filing_date DATE NOT NULL,
                accession_number VARCHAR(50) UNIQUE,
                url TEXT,
                content TEXT,
                risk_factors TEXT,
                management_discussion TEXT,
                financial_statements TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            )
        """)

        # News articles table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR(10) NOT NULL,
                headline TEXT NOT NULL,
                summary TEXT,
                content TEXT,
                source VARCHAR(100),
                author VARCHAR(255),
                published_date TIMESTAMP NOT NULL,
                url TEXT UNIQUE,
                sentiment_score REAL,
                sentiment_label VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            )
        """)

        # M&A events table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ma_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acquirer_ticker VARCHAR(10),
                target_ticker VARCHAR(10),
                acquirer_name VARCHAR(255) NOT NULL,
                target_name VARCHAR(255) NOT NULL,
                announcement_date DATE NOT NULL,
                completion_date DATE,
                deal_value REAL,
                deal_type VARCHAR(50),
                status VARCHAR(50),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Risk scores table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS risk_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                overall_risk_score REAL NOT NULL,
                volatility_score REAL,
                litigation_score REAL,
                sentiment_score REAL,
                financial_anomaly_score REAL,
                regulatory_score REAL,
                risk_level VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, date),
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            )
        """)

        # Risk events table (for timeline visualization)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR(10) NOT NULL,
                event_date DATE NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                event_description TEXT NOT NULL,
                severity VARCHAR(20),
                impact_score REAL,
                source VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            )
        """)

        # Financial metrics table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS financial_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                revenue REAL,
                net_income REAL,
                eps REAL,
                pe_ratio REAL,
                debt_to_equity REAL,
                current_ratio REAL,
                roe REAL,
                roa REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, date),
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            )
        """)

        # Create indices for performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_date ON stock_prices(ticker, date DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_news_ticker_date ON news_articles(ticker, published_date DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_risk_scores_ticker_date ON risk_scores(ticker, date DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sec_filings_ticker_date ON sec_filings(ticker, filing_date DESC)")

    # Company operations
    async def insert_company(self, company_data: Dict[str, Any]) -> int:
        """Insert a new company"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT OR REPLACE INTO companies (ticker, name, sector, industry, market_cap, description, website)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                company_data['ticker'],
                company_data['name'],
                company_data.get('sector'),
                company_data.get('industry'),
                company_data.get('market_cap'),
                company_data.get('description'),
                company_data.get('website')
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_company(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company by ticker"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM companies WHERE ticker = ?", (ticker,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_companies(self) -> List[Dict[str, Any]]:
        """Get all tracked companies"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM companies ORDER BY name")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # Stock price operations
    async def insert_stock_prices(self, prices_data: List[Dict[str, Any]]):
        """Bulk insert stock prices"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany("""
                INSERT OR REPLACE INTO stock_prices (ticker, date, open, high, low, close, volume, adj_close)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    p['ticker'], p['date'], p['open'], p['high'],
                    p['low'], p['close'], p['volume'], p.get('adj_close')
                )
                for p in prices_data
            ])
            await db.commit()

    async def get_stock_prices(self, ticker: str, start_date: str = None, end_date: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get stock prices for a ticker within date range"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            query = "SELECT * FROM stock_prices WHERE ticker = ?"
            params = [ticker]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # News operations
    async def insert_news_article(self, news_data: Dict[str, Any]) -> int:
        """Insert a news article"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT OR IGNORE INTO news_articles
                (ticker, headline, summary, content, source, author, published_date, url, sentiment_score, sentiment_label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                news_data['ticker'],
                news_data['headline'],
                news_data.get('summary'),
                news_data.get('content'),
                news_data.get('source'),
                news_data.get('author'),
                news_data['published_date'],
                news_data.get('url'),
                news_data.get('sentiment_score'),
                news_data.get('sentiment_label')
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_recent_news(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent news for a ticker"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM news_articles
                WHERE ticker = ?
                ORDER BY published_date DESC
                LIMIT ?
            """, (ticker, limit))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # Risk score operations
    async def insert_risk_score(self, risk_data: Dict[str, Any]) -> int:
        """Insert risk score"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT OR REPLACE INTO risk_scores
                (ticker, date, overall_risk_score, volatility_score, litigation_score,
                 sentiment_score, financial_anomaly_score, regulatory_score, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                risk_data['ticker'],
                risk_data['date'],
                risk_data['overall_risk_score'],
                risk_data.get('volatility_score'),
                risk_data.get('litigation_score'),
                risk_data.get('sentiment_score'),
                risk_data.get('financial_anomaly_score'),
                risk_data.get('regulatory_score'),
                risk_data.get('risk_level')
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_risk_timeline(self, ticker: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get risk score timeline for a ticker"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM risk_scores
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT ?
            """, (ticker, days))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def close(self):
        """Close database connection"""
        # aiosqlite doesn't maintain persistent connections
        pass


# Global instance
db_manager = SQLiteManager()
