"""
SEC Edgar Data Ingestion Service
Fetches and parses SEC filings (10-K, 10-Q, 8-K) for risk analysis
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from pathlib import Path
import asyncio

from app.config import settings, RAW_DATA_DIR

logger = logging.getLogger(__name__)


class SECEdgarService:
    """Service for fetching SEC Edgar filings"""

    def __init__(self):
        self.base_url = "https://www.sec.gov"
        self.headers = {
            'User-Agent': settings.SEC_EDGAR_USER_AGENT
        }
        self.filings_dir = RAW_DATA_DIR / "sec_filings"
        self.filings_dir.mkdir(parents=True, exist_ok=True)

    def get_company_cik(self, ticker: str) -> Optional[str]:
        """Get CIK (Central Index Key) for a company"""
        try:
            # Search for company ticker
            url = f"{self.base_url}/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'CIK': ticker,
                'type': '',
                'dateb': '',
                'owner': 'exclude',
                'output': 'atom',
                'count': '1'
            }

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            # Parse XML response to extract CIK
            soup = BeautifulSoup(response.content, 'xml')
            cik_elem = soup.find('CIK')

            if cik_elem:
                cik = cik_elem.text.zfill(10)  # Pad with zeros to 10 digits
                logger.info(f"Found CIK {cik} for ticker {ticker}")
                return cik

            logger.warning(f"Could not find CIK for ticker {ticker}")
            return None

        except Exception as e:
            logger.error(f"Error getting CIK for {ticker}: {e}")
            return None

    def fetch_company_filings(
        self,
        ticker: str,
        filing_type: str = "10-K",
        num_filings: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent filings for a company

        Args:
            ticker: Stock ticker
            filing_type: Type of filing (10-K, 10-Q, 8-K, etc.)
            num_filings: Number of recent filings to fetch
        """
        try:
            cik = self.get_company_cik(ticker)
            if not cik:
                return []

            # Fetch filings list
            url = f"{self.base_url}/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'type': filing_type,
                'dateb': '',
                'owner': 'exclude',
                'output': 'xml',
                'count': str(num_filings)
            }

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            # Parse XML
            soup = BeautifulSoup(response.content, 'xml')
            filings = []

            for entry in soup.find_all('filing'):
                filing_data = {
                    'ticker': ticker,
                    'filing_type': entry.find('filingType').text if entry.find('filingType') else filing_type,
                    'filing_date': entry.find('filingDate').text if entry.find('filingDate') else None,
                    'accession_number': entry.find('accessionNumber').text.replace('-', '') if entry.find('accessionNumber') else None,
                    'url': entry.find('filingHref').text if entry.find('filingHref') else None
                }
                filings.append(filing_data)

            logger.info(f"Found {len(filings)} {filing_type} filings for {ticker}")
            return filings

        except Exception as e:
            logger.error(f"Error fetching filings for {ticker}: {e}")
            return []

    def download_filing(self, filing_url: str) -> Optional[str]:
        """Download and extract text from filing"""
        try:
            response = requests.get(filing_url, headers=self.headers)
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract text content
            text = soup.get_text()

            # Clean up text
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Remove multiple blank lines
            text = text.strip()

            return text

        except Exception as e:
            logger.error(f"Error downloading filing from {filing_url}: {e}")
            return None

    def extract_risk_factors(self, filing_text: str) -> Optional[str]:
        """
        Extract Risk Factors section from 10-K filing

        Item 1A in 10-K contains Risk Factors
        """
        if not filing_text:
            return None

        try:
            # Pattern to match Risk Factors section
            patterns = [
                r'Item\s+1A\.\s*Risk\s+Factors(.*?)Item\s+1B\.',
                r'Item\s+1A\.\s*Risk\s+Factors(.*?)Item\s+2\.',
                r'ITEM\s+1A\.\s*RISK\s+FACTORS(.*?)ITEM\s+1B\.',
                r'ITEM\s+1A\.\s*RISK\s+FACTORS(.*?)ITEM\s+2\.',
            ]

            for pattern in patterns:
                match = re.search(pattern, filing_text, re.IGNORECASE | re.DOTALL)
                if match:
                    risk_factors = match.group(1).strip()
                    logger.info(f"Extracted risk factors ({len(risk_factors)} chars)")
                    return risk_factors

            logger.warning("Could not extract risk factors section")
            return None

        except Exception as e:
            logger.error(f"Error extracting risk factors: {e}")
            return None

    def extract_md_and_a(self, filing_text: str) -> Optional[str]:
        """
        Extract Management Discussion and Analysis section

        Item 7 in 10-K contains MD&A
        """
        if not filing_text:
            return None

        try:
            patterns = [
                r'Item\s+7\.\s*Management.*?Discussion.*?Analysis(.*?)Item\s+8\.',
                r'ITEM\s+7\.\s*MANAGEMENT.*?DISCUSSION.*?ANALYSIS(.*?)ITEM\s+8\.',
            ]

            for pattern in patterns:
                match = re.search(pattern, filing_text, re.IGNORECASE | re.DOTALL)
                if match:
                    mda = match.group(1).strip()
                    logger.info(f"Extracted MD&A ({len(mda)} chars)")
                    return mda

            logger.warning("Could not extract MD&A section")
            return None

        except Exception as e:
            logger.error(f"Error extracting MD&A: {e}")
            return None

    async def process_filing(self, ticker: str, filing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single filing and extract relevant sections"""
        try:
            # Download filing content
            filing_text = self.download_filing(filing_data['url'])

            if not filing_text:
                return None

            # Extract sections
            risk_factors = self.extract_risk_factors(filing_text)
            mda = self.extract_md_and_a(filing_text)

            # Save raw filing to disk
            filing_file = self.filings_dir / f"{ticker}_{filing_data['accession_number']}.txt"
            with open(filing_file, 'w', encoding='utf-8') as f:
                f.write(filing_text)

            processed_data = {
                'ticker': ticker,
                'filing_type': filing_data['filing_type'],
                'filing_date': filing_data['filing_date'],
                'accession_number': filing_data['accession_number'],
                'url': filing_data['url'],
                'content': filing_text[:50000],  # Store first 50k chars in DB
                'risk_factors': risk_factors,
                'management_discussion': mda,
                'file_path': str(filing_file)
            }

            logger.info(f"Processed {filing_data['filing_type']} for {ticker}")
            return processed_data

        except Exception as e:
            logger.error(f"Error processing filing for {ticker}: {e}")
            return None

    async def fetch_and_process_10k(self, ticker: str, num_filings: int = 3) -> List[Dict[str, Any]]:
        """Fetch and process 10-K filings for a company"""
        try:
            # Fetch filings metadata
            filings = self.fetch_company_filings(ticker, filing_type="10-K", num_filings=num_filings)

            if not filings:
                logger.warning(f"No 10-K filings found for {ticker}")
                return []

            # Process each filing
            processed_filings = []
            for filing in filings:
                # Add delay to respect SEC rate limits (10 requests per second max)
                await asyncio.sleep(0.2)

                processed = await self.process_filing(ticker, filing)
                if processed:
                    processed_filings.append(processed)

            logger.info(f"Processed {len(processed_filings)} 10-K filings for {ticker}")
            return processed_filings

        except Exception as e:
            logger.error(f"Error fetching 10-K for {ticker}: {e}")
            return []

    async def fetch_all_filings_for_tickers(self, tickers: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch filings for multiple tickers"""
        results = {}

        for ticker in tickers:
            try:
                filings = await self.fetch_and_process_10k(ticker, num_filings=2)
                results[ticker] = filings
                logger.info(f"Fetched filings for {ticker}")

                # Respect rate limits
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                results[ticker] = []

        return results


# Global instance
sec_edgar = SECEdgarService()
