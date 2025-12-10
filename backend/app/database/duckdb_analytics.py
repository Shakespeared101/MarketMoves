"""
DuckDB Analytics Module for MarketMoves
High-performance columnar analytics for financial data
"""

import duckdb
from typing import List, Dict, Any, Optional
import pandas as pd
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class DuckDBAnalytics:
    """Manages DuckDB connections and analytical queries"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DUCKDB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    def connect(self):
        """Establish DuckDB connection"""
        if not self.conn:
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"Connected to DuckDB at {self.db_path}")
        return self.conn

    def close(self):
        """Close DuckDB connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def load_from_sqlite(self, sqlite_path: str):
        """Load data from SQLite into DuckDB for analytics"""
        conn = self.connect()

        # Attach SQLite database
        conn.execute(f"ATTACH '{sqlite_path}' AS sqlite_db (TYPE SQLITE)")

        # Copy tables to DuckDB for faster analytics
        tables = ['companies', 'stock_prices', 'news_articles', 'risk_scores', 'financial_metrics']

        for table in tables:
            try:
                conn.execute(f"""
                    CREATE OR REPLACE TABLE {table} AS
                    SELECT * FROM sqlite_db.{table}
                """)
                logger.info(f"Loaded {table} into DuckDB")
            except Exception as e:
                logger.warning(f"Could not load {table}: {e}")

    # Volatility Analysis
    def calculate_volatility_metrics(self, ticker: str = None, days: int = 30) -> pd.DataFrame:
        """Calculate volatility metrics for stocks"""
        conn = self.connect()

        where_clause = f"WHERE ticker = '{ticker}'" if ticker else ""

        query = f"""
            WITH daily_returns AS (
                SELECT
                    ticker,
                    date,
                    close,
                    LAG(close) OVER (PARTITION BY ticker ORDER BY date) as prev_close,
                    (close - LAG(close) OVER (PARTITION BY ticker ORDER BY date)) /
                        LAG(close) OVER (PARTITION BY ticker ORDER BY date) as daily_return
                FROM stock_prices
                {where_clause}
                ORDER BY date DESC
                LIMIT {days}
            )
            SELECT
                ticker,
                AVG(daily_return) as avg_return,
                STDDEV(daily_return) as volatility,
                MIN(daily_return) as min_return,
                MAX(daily_return) as max_return,
                AVG(daily_return) / NULLIF(STDDEV(daily_return), 0) as sharpe_approx
            FROM daily_returns
            WHERE daily_return IS NOT NULL
            GROUP BY ticker
            ORDER BY volatility DESC
        """

        return conn.execute(query).df()

    # Correlation Analysis
    def calculate_correlation_matrix(self, tickers: List[str], days: int = 90) -> pd.DataFrame:
        """Calculate correlation matrix between stocks"""
        conn = self.connect()

        # Build pivot table of returns
        tickers_str = "', '".join(tickers)

        query = f"""
            WITH daily_returns AS (
                SELECT
                    date,
                    ticker,
                    (close - LAG(close) OVER (PARTITION BY ticker ORDER BY date)) /
                        LAG(close) OVER (PARTITION BY ticker ORDER BY date) as return
                FROM stock_prices
                WHERE ticker IN ('{tickers_str}')
                    AND date >= CURRENT_DATE - INTERVAL '{days} days'
            )
            SELECT * FROM daily_returns
            WHERE return IS NOT NULL
            ORDER BY date
        """

        df = conn.execute(query).df()

        if not df.empty:
            # Pivot and calculate correlation
            pivot_df = df.pivot(index='date', columns='ticker', values='return')
            correlation_matrix = pivot_df.corr()
            return correlation_matrix

        return pd.DataFrame()

    # Sector Performance Analysis
    def analyze_sector_performance(self, days: int = 30) -> pd.DataFrame:
        """Analyze performance by sector"""
        conn = self.connect()

        query = f"""
            WITH recent_prices AS (
                SELECT
                    sp.ticker,
                    c.sector,
                    sp.date,
                    sp.close,
                    FIRST_VALUE(sp.close) OVER (
                        PARTITION BY sp.ticker
                        ORDER BY sp.date
                    ) as start_price
                FROM stock_prices sp
                JOIN companies c ON sp.ticker = c.ticker
                WHERE sp.date >= CURRENT_DATE - INTERVAL '{days} days'
                    AND c.sector IS NOT NULL
            )
            SELECT
                sector,
                COUNT(DISTINCT ticker) as num_stocks,
                AVG((close - start_price) / start_price * 100) as avg_return_pct,
                STDDEV((close - start_price) / start_price * 100) as volatility,
                MIN((close - start_price) / start_price * 100) as min_return,
                MAX((close - start_price) / start_price * 100) as max_return
            FROM recent_prices
            GROUP BY sector
            ORDER BY avg_return_pct DESC
        """

        return conn.execute(query).df()

    # Risk Aggregation
    def aggregate_risk_scores(self, ticker: str = None, days: int = 90) -> pd.DataFrame:
        """Aggregate risk scores over time"""
        conn = self.connect()

        where_clause = f"WHERE ticker = '{ticker}'" if ticker else ""

        query = f"""
            SELECT
                ticker,
                DATE_TRUNC('week', date) as week,
                AVG(overall_risk_score) as avg_risk,
                MAX(overall_risk_score) as max_risk,
                MIN(overall_risk_score) as min_risk,
                AVG(volatility_score) as avg_volatility,
                AVG(sentiment_score) as avg_sentiment
            FROM risk_scores
            {where_clause}
            WHERE date >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY ticker, week
            ORDER BY week DESC
        """

        return conn.execute(query).df()

    # Sentiment Trends
    def analyze_sentiment_trends(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """Analyze news sentiment trends"""
        conn = self.connect()

        query = f"""
            SELECT
                DATE_TRUNC('day', published_date) as date,
                COUNT(*) as article_count,
                AVG(sentiment_score) as avg_sentiment,
                STDDEV(sentiment_score) as sentiment_volatility,
                SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
            FROM news_articles
            WHERE ticker = '{ticker}'
                AND published_date >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY date
            ORDER BY date DESC
        """

        return conn.execute(query).df()

    # Anomaly Detection
    def detect_price_anomalies(self, ticker: str, std_dev_threshold: float = 2.0) -> pd.DataFrame:
        """Detect price anomalies using statistical methods"""
        conn = self.connect()

        query = f"""
            WITH price_stats AS (
                SELECT
                    ticker,
                    date,
                    close,
                    AVG(close) OVER (
                        PARTITION BY ticker
                        ORDER BY date
                        ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
                    ) as moving_avg,
                    STDDEV(close) OVER (
                        PARTITION BY ticker
                        ORDER BY date
                        ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
                    ) as moving_std
                FROM stock_prices
                WHERE ticker = '{ticker}'
            )
            SELECT
                date,
                close,
                moving_avg,
                moving_std,
                (close - moving_avg) / NULLIF(moving_std, 0) as z_score,
                CASE
                    WHEN ABS((close - moving_avg) / NULLIF(moving_std, 0)) > {std_dev_threshold}
                    THEN true
                    ELSE false
                END as is_anomaly
            FROM price_stats
            WHERE moving_std IS NOT NULL
            ORDER BY date DESC
            LIMIT 100
        """

        return conn.execute(query).df()

    # M&A Analysis
    def analyze_ma_activity(self, time_period: str = '1 year') -> pd.DataFrame:
        """Analyze M&A activity and trends"""
        conn = self.connect()

        query = f"""
            SELECT
                DATE_TRUNC('month', announcement_date) as month,
                COUNT(*) as deal_count,
                SUM(deal_value) as total_value,
                AVG(deal_value) as avg_deal_value,
                deal_type,
                status
            FROM ma_events
            WHERE announcement_date >= CURRENT_DATE - INTERVAL '{time_period}'
            GROUP BY month, deal_type, status
            ORDER BY month DESC
        """

        return conn.execute(query).df()

    # Financial Metrics Analysis
    def analyze_financial_health(self, ticker: str) -> Dict[str, Any]:
        """Analyze financial health indicators"""
        conn = self.connect()

        query = f"""
            WITH latest_metrics AS (
                SELECT *
                FROM financial_metrics
                WHERE ticker = '{ticker}'
                ORDER BY date DESC
                LIMIT 4
            )
            SELECT
                AVG(pe_ratio) as avg_pe,
                AVG(debt_to_equity) as avg_debt_equity,
                AVG(current_ratio) as avg_current_ratio,
                AVG(roe) as avg_roe,
                AVG(roa) as avg_roa,
                (MAX(revenue) - MIN(revenue)) / NULLIF(MIN(revenue), 0) * 100 as revenue_growth_pct
            FROM latest_metrics
        """

        result = conn.execute(query).df()
        return result.to_dict('records')[0] if not result.empty else {}

    # Custom Query Execution
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute custom analytical query"""
        conn = self.connect()
        return conn.execute(query).df()


# Global instance
analytics = DuckDBAnalytics()
