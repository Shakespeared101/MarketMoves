"""
Risk Engine
Multi-factor risk scoring and analysis
"""

import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from app.config import settings
from app.database.sqlite_manager import db_manager
from app.database.duckdb_analytics import analytics
from app.database.neo4j_manager import neo4j_manager

logger = logging.getLogger(__name__)


class RiskEngine:
    """Engine for calculating and analyzing risk scores"""

    def __init__(self):
        # Risk weights from config
        self.weight_volatility = settings.RISK_WEIGHT_VOLATILITY
        self.weight_litigation = settings.RISK_WEIGHT_LITIGATION
        self.weight_sentiment = settings.RISK_WEIGHT_SENTIMENT
        self.weight_financial = settings.RISK_WEIGHT_FINANCIAL_ANOMALY
        self.weight_regulatory = settings.RISK_WEIGHT_REGULATORY

    def calculate_volatility_score(self, ticker: str, days: int = 30) -> float:
        """
        Calculate volatility-based risk score (0-10)

        Higher volatility = higher risk
        """
        try:
            # Get volatility metrics from DuckDB
            df = analytics.calculate_volatility_metrics(ticker=ticker, days=days)

            if df.empty:
                return 5.0  # Default medium risk

            volatility = df.iloc[0]['volatility']

            # Normalize to 0-10 scale
            # Assume volatility of 0.03 (3%) is medium (5), 0.06 (6%) is high (10)
            score = min(10.0, (volatility / 0.03) * 5.0)

            return round(score, 2)

        except Exception as e:
            logger.error(f"Error calculating volatility score for {ticker}: {e}")
            return 5.0

    async def calculate_sentiment_score(self, ticker: str) -> float:
        """
        Calculate sentiment-based risk score (0-10)

        Negative sentiment = higher risk
        """
        try:
            # Get recent news
            articles = await db_manager.get_recent_news(ticker, limit=50)

            if not articles:
                return 5.0  # Neutral

            # Calculate average sentiment
            sentiments = [a['sentiment_score'] for a in articles if a.get('sentiment_score') is not None]

            if not sentiments:
                return 5.0

            avg_sentiment = sum(sentiments) / len(sentiments)

            # Convert sentiment (-1 to 1) to risk score (0-10)
            # -1 (very negative) = 10 (high risk)
            # 0 (neutral) = 5 (medium risk)
            # 1 (very positive) = 0 (low risk)
            score = 5.0 - (avg_sentiment * 5.0)

            return round(max(0, min(10, score)), 2)

        except Exception as e:
            logger.error(f"Error calculating sentiment score for {ticker}: {e}")
            return 5.0

    async def calculate_litigation_score(self, ticker: str) -> float:
        """
        Calculate litigation risk score (0-10)

        Based on number and severity of lawsuits (from Neo4j graph)
        """
        try:
            # Check if Neo4j is available
            if not neo4j_manager.driver:
                logger.warning(f"Neo4j unavailable for litigation score - using default")
                return 3.0

            # Query Neo4j for lawsuit data
            lawsuit_data = await neo4j_manager.get_lawsuits_for_risk(ticker)

            lawsuit_count = lawsuit_data.get('lawsuit_count', 0)
            avg_impact = lawsuit_data.get('avg_impact', 0.0)
            high_severity_count = lawsuit_data.get('high_severity_count', 0)

            if lawsuit_count == 0:
                return 1.0  # Low risk - no active lawsuits

            # Calculate score based on:
            # - Number of lawsuits (0-5 points)
            # - Average impact (0-3 points)
            # - High severity count (0-2 points)

            count_score = min(5.0, (lawsuit_count / 5.0) * 5.0)  # 5+ lawsuits = 5 points
            impact_score = min(3.0, (avg_impact / 5.0) * 3.0)     # Impact 5+ = 3 points
            severity_score = min(2.0, (high_severity_count / 3.0) * 2.0)  # 3+ high severity = 2 points

            total_score = count_score + impact_score + severity_score

            logger.info(
                f"Litigation score for {ticker}: {total_score:.2f} "
                f"(lawsuits: {lawsuit_count}, avg_impact: {avg_impact:.2f}, "
                f"high_severity: {high_severity_count})"
            )

            return round(total_score, 2)

        except Exception as e:
            logger.error(f"Error calculating litigation score for {ticker}: {e}")
            return 3.0

    def calculate_financial_anomaly_score(self, ticker: str) -> float:
        """
        Calculate financial anomaly score (0-10)

        Based on unusual patterns in financial metrics
        """
        try:
            # Get price anomalies
            df = analytics.detect_price_anomalies(ticker, std_dev_threshold=2.0)

            if df.empty:
                return 2.0

            # Count recent anomalies (last 30 days)
            recent_anomalies = df.head(30)
            anomaly_count = recent_anomalies['is_anomaly'].sum()

            # Normalize: 0 anomalies = 0, 10+ anomalies = 10
            score = min(10.0, (anomaly_count / 10.0) * 10.0)

            return round(score, 2)

        except Exception as e:
            logger.error(f"Error calculating financial anomaly score for {ticker}: {e}")
            return 2.0

    def calculate_regulatory_score(self, ticker: str) -> float:
        """
        Calculate regulatory risk score (0-10)

        Based on regulatory penalties and compliance issues
        """
        try:
            # TODO: Implement regulatory data tracking
            # Placeholder
            return 2.0

        except Exception as e:
            logger.error(f"Error calculating regulatory score for {ticker}: {e}")
            return 2.0

    async def calculate_overall_risk(self, ticker: str) -> Dict[str, Any]:
        """
        Calculate overall risk score combining all factors

        Returns:
            Dictionary with overall score and component scores
        """
        try:
            # Calculate individual scores
            volatility_score = self.calculate_volatility_score(ticker)
            sentiment_score = await self.calculate_sentiment_score(ticker)
            litigation_score = await self.calculate_litigation_score(ticker)
            financial_score = self.calculate_financial_anomaly_score(ticker)
            regulatory_score = self.calculate_regulatory_score(ticker)

            # Calculate weighted overall score
            overall_score = (
                volatility_score * self.weight_volatility +
                litigation_score * self.weight_litigation +
                sentiment_score * self.weight_sentiment +
                financial_score * self.weight_financial +
                regulatory_score * self.weight_regulatory
            )

            overall_score = round(overall_score, 2)

            # Determine risk level
            if overall_score < 3:
                risk_level = "Low"
            elif overall_score < 6:
                risk_level = "Medium"
            elif overall_score < 8:
                risk_level = "High"
            else:
                risk_level = "Critical"

            result = {
                'ticker': ticker,
                'overall_risk_score': overall_score,
                'risk_level': risk_level,
                'components': {
                    'volatility_score': volatility_score,
                    'sentiment_score': sentiment_score,
                    'litigation_score': litigation_score,
                    'financial_anomaly_score': financial_score,
                    'regulatory_score': regulatory_score
                },
                'weights': {
                    'volatility': self.weight_volatility,
                    'litigation': self.weight_litigation,
                    'sentiment': self.weight_sentiment,
                    'financial_anomaly': self.weight_financial,
                    'regulatory': self.weight_regulatory
                },
                'calculated_at': datetime.now().isoformat()
            }

            # Store in database
            await self._store_risk_score(ticker, result)

            logger.info(f"Calculated risk score for {ticker}: {overall_score} ({risk_level})")
            return result

        except Exception as e:
            logger.error(f"Error calculating overall risk for {ticker}: {e}")
            return {
                'ticker': ticker,
                'overall_risk_score': 5.0,
                'risk_level': "Unknown",
                'error': str(e)
            }

    async def _store_risk_score(self, ticker: str, risk_data: Dict[str, Any]):
        """Store calculated risk score in database"""
        try:
            components = risk_data['components']

            risk_record = {
                'ticker': ticker,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'overall_risk_score': risk_data['overall_risk_score'],
                'volatility_score': components['volatility_score'],
                'litigation_score': components['litigation_score'],
                'sentiment_score': components['sentiment_score'],
                'financial_anomaly_score': components['financial_anomaly_score'],
                'regulatory_score': components['regulatory_score'],
                'risk_level': risk_data['risk_level']
            }

            await db_manager.insert_risk_score(risk_record)

        except Exception as e:
            logger.error(f"Error storing risk score for {ticker}: {e}")

    async def get_risk_timeline(self, ticker: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get historical risk scores for timeline visualization"""
        try:
            return await db_manager.get_risk_timeline(ticker, days=days)
        except Exception as e:
            logger.error(f"Error getting risk timeline for {ticker}: {e}")
            return []

    async def calculate_risk_for_multiple_tickers(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Calculate risk scores for multiple tickers"""
        results = {}

        for ticker in tickers:
            try:
                risk_data = await self.calculate_overall_risk(ticker)
                results[ticker] = risk_data
            except Exception as e:
                logger.error(f"Error calculating risk for {ticker}: {e}")
                results[ticker] = {'error': str(e)}

        return results


# Global instance
risk_engine = RiskEngine()
