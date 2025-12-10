"""
News Fetcher Service
Fetches corporate news from multiple sources and performs sentiment analysis
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.config import settings
from app.database.sqlite_manager import db_manager

logger = logging.getLogger(__name__)


class NewsFetcherService:
    """Service for fetching and analyzing corporate news"""

    def __init__(self):
        self.newsapi_key = settings.NEWSAPI_KEY
        self.newsapi_url = "https://newsapi.org/v2"
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using VADER

        Returns:
            Dictionary with scores and label
        """
        scores = self.sentiment_analyzer.polarity_scores(text)

        # Determine label based on compound score
        compound = scores['compound']
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'

        return {
            'score': compound,
            'label': label,
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu']
        }

    async def fetch_news_from_newsapi(
        self,
        query: str,
        days_back: int = 7,
        language: str = 'en'
    ) -> List[Dict[str, Any]]:
        """
        Fetch news from NewsAPI

        Args:
            query: Search query (company name or ticker)
            days_back: Number of days to look back
            language: Language code
        """
        if not self.newsapi_key:
            logger.warning("NewsAPI key not configured")
            return []

        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days_back)

            params = {
                'q': query,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'language': language,
                'sortBy': 'publishedAt',
                'apiKey': self.newsapi_key,
                'pageSize': 100
            }

            response = requests.get(f"{self.newsapi_url}/everything", params=params)
            response.raise_for_status()

            data = response.json()
            articles = data.get('articles', [])

            logger.info(f"Fetched {len(articles)} articles for query: {query}")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news from NewsAPI: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_news_from_newsapi: {e}")
            return []

    async def fetch_company_news(
        self,
        ticker: str,
        company_name: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch news for a specific company

        Args:
            ticker: Stock ticker
            company_name: Company name for search
            days_back: Days to look back
        """
        # Try with company name first
        articles = await self.fetch_news_from_newsapi(company_name, days_back=days_back)

        # If not enough results, try with ticker
        if len(articles) < 5:
            ticker_articles = await self.fetch_news_from_newsapi(ticker, days_back=days_back)
            articles.extend(ticker_articles)

        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []

        for article in articles:
            url = article.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        logger.info(f"Found {len(unique_articles)} unique articles for {ticker}")
        return unique_articles

    async def process_and_store_article(self, ticker: str, article: Dict[str, Any]) -> bool:
        """
        Process article, analyze sentiment, and store in database

        Args:
            ticker: Stock ticker
            article: Article data from news API
        """
        try:
            # Combine title and description for sentiment analysis
            text_for_sentiment = f"{article.get('title', '')} {article.get('description', '')}"
            sentiment = self.analyze_sentiment(text_for_sentiment)

            # Prepare article data
            news_data = {
                'ticker': ticker,
                'headline': article.get('title', ''),
                'summary': article.get('description'),
                'content': article.get('content'),
                'source': article.get('source', {}).get('name'),
                'author': article.get('author'),
                'published_date': article.get('publishedAt'),
                'url': article.get('url'),
                'sentiment_score': sentiment['score'],
                'sentiment_label': sentiment['label']
            }

            # Store in database
            await db_manager.insert_news_article(news_data)
            return True

        except Exception as e:
            logger.error(f"Error processing article for {ticker}: {e}")
            return False

    async def fetch_and_store_company_news(
        self,
        ticker: str,
        company_name: str,
        days_back: int = 30
    ) -> int:
        """
        Fetch news for a company and store in database

        Returns:
            Number of articles stored
        """
        try:
            # Fetch articles
            articles = await self.fetch_company_news(ticker, company_name, days_back)

            # Process and store each article
            stored_count = 0
            for article in articles:
                success = await self.process_and_store_article(ticker, article)
                if success:
                    stored_count += 1

            logger.info(f"Stored {stored_count} articles for {ticker}")
            return stored_count

        except Exception as e:
            logger.error(f"Error in fetch_and_store_company_news for {ticker}: {e}")
            return 0

    async def update_news_for_tickers(self, tickers: List[str]) -> Dict[str, int]:
        """
        Update news for multiple tickers

        Args:
            tickers: List of stock tickers

        Returns:
            Dictionary with ticker -> article count
        """
        results = {}

        for ticker in tickers:
            try:
                # Get company name from database
                company = await db_manager.get_company(ticker)

                if not company:
                    logger.warning(f"Company {ticker} not found in database")
                    results[ticker] = 0
                    continue

                company_name = company['name']

                # Fetch and store news
                count = await self.fetch_and_store_company_news(ticker, company_name, days_back=7)
                results[ticker] = count

                logger.info(f"Updated news for {ticker}: {count} articles")

            except Exception as e:
                logger.error(f"Error updating news for {ticker}: {e}")
                results[ticker] = 0

        return results

    async def get_sentiment_summary(self, ticker: str, days: int = 30) -> Dict[str, Any]:
        """
        Get sentiment summary for a ticker

        Args:
            ticker: Stock ticker
            days: Number of days to analyze

        Returns:
            Sentiment statistics
        """
        try:
            # Get recent news from database
            articles = await db_manager.get_recent_news(ticker, limit=100)

            if not articles:
                return {
                    'ticker': ticker,
                    'article_count': 0,
                    'average_sentiment': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0
                }

            # Calculate statistics
            sentiments = [a['sentiment_score'] for a in articles if a.get('sentiment_score') is not None]
            labels = [a['sentiment_label'] for a in articles if a.get('sentiment_label')]

            summary = {
                'ticker': ticker,
                'article_count': len(articles),
                'average_sentiment': sum(sentiments) / len(sentiments) if sentiments else 0,
                'positive_count': labels.count('positive'),
                'negative_count': labels.count('negative'),
                'neutral_count': labels.count('neutral'),
                'sentiment_trend': 'positive' if sum(sentiments) > 0 else 'negative' if sum(sentiments) < 0 else 'neutral'
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting sentiment summary for {ticker}: {e}")
            return {}


# Global instance
news_fetcher = NewsFetcherService()
