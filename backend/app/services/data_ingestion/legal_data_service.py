"""
Legal Data Service for MarketMoves
Generates legal events, lawsuits, and regulatory actions for companies
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import uuid

from app.database.neo4j_manager import neo4j_manager

logger = logging.getLogger(__name__)


class LegalDataService:
    """Service for generating and managing legal data"""

    def __init__(self):
        self.lawsuit_templates = {
            'Securities Fraud': {
                'severity': 'High',
                'typical_duration_months': 24,
                'impact_range': (3.5, 4.8)
            },
            'Antitrust Violation': {
                'severity': 'High',
                'typical_duration_months': 36,
                'impact_range': (4.0, 4.9)
            },
            'Patent Infringement': {
                'severity': 'Medium',
                'typical_duration_months': 18,
                'impact_range': (2.5, 3.8)
            },
            'Labor Dispute': {
                'severity': 'Medium',
                'typical_duration_months': 12,
                'impact_range': (2.0, 3.5)
            },
            'Environmental Violation': {
                'severity': 'Medium',
                'typical_duration_months': 20,
                'impact_range': (2.8, 4.2)
            },
            'Consumer Protection': {
                'severity': 'Medium',
                'typical_duration_months': 15,
                'impact_range': (2.3, 3.6)
            },
            'Regulatory Fine': {
                'severity': 'Low',
                'typical_duration_months': 6,
                'impact_range': (1.5, 2.8)
            },
            'Breach of Contract': {
                'severity': 'Low',
                'typical_duration_months': 10,
                'impact_range': (1.8, 3.0)
            }
        }

    def generate_lawsuits(self, ticker: str, company_name: str, count: int = 3) -> List[Dict[str, Any]]:
        """Generate realistic lawsuit data for a company"""
        lawsuits = []
        end_date = datetime.now()

        for i in range(count):
            lawsuit_type = random.choice(list(self.lawsuit_templates.keys()))
            template = self.lawsuit_templates[lawsuit_type]

            # Generate dates
            filed_date = end_date - timedelta(days=random.randint(30, 730))
            duration = template['typical_duration_months'] + random.randint(-6, 6)

            # Random status based on how old the lawsuit is
            days_old = (end_date - filed_date).days
            if days_old > duration * 30:
                status = random.choice(['Settled', 'Dismissed', 'Closed'])
                resolved_date = filed_date + timedelta(days=duration * 30)
            elif days_old > duration * 15:
                status = 'In Litigation'
                resolved_date = None
            else:
                status = 'Filed'
                resolved_date = None

            # Generate impact score
            min_impact, max_impact = template['impact_range']
            impact_score = round(random.uniform(min_impact, max_impact), 2)

            lawsuit = {
                'id': str(uuid.uuid4()),
                'ticker': ticker,
                'company_name': company_name,
                'title': f"{lawsuit_type} Case #{1000 + i}",
                'lawsuit_type': lawsuit_type,
                'description': self._generate_description(lawsuit_type, company_name),
                'filed_date': filed_date.strftime('%Y-%m-%d'),
                'resolved_date': resolved_date.strftime('%Y-%m-%d') if resolved_date else None,
                'status': status,
                'severity': template['severity'],
                'impact_score': impact_score,
                'plaintiff': self._generate_plaintiff(lawsuit_type),
                'jurisdiction': random.choice(['Federal', 'State', 'International']),
                'estimated_liability': self._estimate_liability(lawsuit_type, template['severity'])
            }

            lawsuits.append(lawsuit)

        logger.info(f"Generated {len(lawsuits)} lawsuits for {ticker}")
        return lawsuits

    def generate_regulatory_actions(self, ticker: str, company_name: str, count: int = 2) -> List[Dict[str, Any]]:
        """Generate regulatory action data"""
        actions = []
        end_date = datetime.now()

        agencies = ['SEC', 'FTC', 'EPA', 'DOJ', 'FCC', 'FDA']
        action_types = [
            'Investigation',
            'Fine',
            'Consent Decree',
            'Warning Letter',
            'Enforcement Action'
        ]

        for i in range(count):
            action_date = end_date - timedelta(days=random.randint(30, 365))
            action_type = random.choice(action_types)
            agency = random.choice(agencies)

            action = {
                'id': str(uuid.uuid4()),
                'ticker': ticker,
                'company_name': company_name,
                'agency': agency,
                'action_type': action_type,
                'date': action_date.strftime('%Y-%m-%d'),
                'description': f"{agency} {action_type} regarding compliance matters",
                'severity': random.choice(['Low', 'Medium', 'High']),
                'fine_amount': random.randint(100000, 50000000) if action_type == 'Fine' else None,
                'status': random.choice(['Active', 'Resolved', 'Under Review'])
            }

            actions.append(action)

        logger.info(f"Generated {len(actions)} regulatory actions for {ticker}")
        return actions

    def generate_executive_connections(self, ticker: str, company_name: str) -> List[Dict[str, Any]]:
        """Generate executive and board member data"""
        positions = [
            'CEO',
            'CFO',
            'COO',
            'CTO',
            'Board Member',
            'General Counsel',
            'Chief Risk Officer'
        ]

        executives = []
        for i, position in enumerate(positions[:5]):  # 5 key executives
            executive = {
                'id': str(uuid.uuid4()),
                'name': f"Executive {chr(65 + i)}",  # Executive A, B, C...
                'position': position,
                'company_ticker': ticker,
                'company_name': company_name,
                'tenure_years': random.randint(1, 15),
                'background': random.choice([
                    'Finance',
                    'Technology',
                    'Legal',
                    'Operations',
                    'Marketing'
                ])
            }
            executives.append(executive)

        return executives

    def generate_subsidiaries(self, ticker: str, company_name: str, count: int = 3) -> List[Dict[str, Any]]:
        """Generate subsidiary company data"""
        subsidiaries = []

        for i in range(count):
            subsidiary = {
                'id': str(uuid.uuid4()),
                'name': f"{company_name} {random.choice(['Technologies', 'International', 'Services', 'Solutions', 'Group'])} {i+1}",
                'parent_ticker': ticker,
                'industry': random.choice(['Technology', 'Services', 'Manufacturing', 'Retail']),
                'location': random.choice(['USA', 'Europe', 'Asia', 'South America']),
                'ownership_percentage': random.randint(51, 100)
            }
            subsidiaries.append(subsidiary)

        return subsidiaries

    def _generate_description(self, lawsuit_type: str, company_name: str) -> str:
        """Generate a realistic lawsuit description"""
        descriptions = {
            'Securities Fraud': f"Shareholders allege that {company_name} made materially false and misleading statements regarding business operations and financial results.",
            'Antitrust Violation': f"Regulatory authorities investigate {company_name} for potential anti-competitive practices and market manipulation.",
            'Patent Infringement': f"Patent holder claims {company_name} products infringe on proprietary technology and intellectual property.",
            'Labor Dispute': f"Former employees file class action lawsuit against {company_name} regarding workplace conditions and compensation.",
            'Environmental Violation': f"{company_name} faces allegations of environmental regulation violations and improper waste disposal.",
            'Consumer Protection': f"Consumers allege {company_name} engaged in deceptive marketing practices and false advertising.",
            'Regulatory Fine': f"Regulatory agency imposes fine on {company_name} for compliance violations.",
            'Breach of Contract': f"Business partner alleges {company_name} failed to fulfill contractual obligations."
        }
        return descriptions.get(lawsuit_type, f"Legal matter involving {company_name}")

    def _generate_plaintiff(self, lawsuit_type: str) -> str:
        """Generate plaintiff name based on lawsuit type"""
        if lawsuit_type in ['Securities Fraud', 'Labor Dispute', 'Consumer Protection']:
            return f"Class Action Plaintiffs"
        elif lawsuit_type in ['Antitrust Violation', 'Environmental Violation', 'Regulatory Fine']:
            return random.choice(['Department of Justice', 'SEC', 'FTC', 'EPA'])
        else:
            return f"Private Plaintiff Group"

    def _estimate_liability(self, lawsuit_type: str, severity: str) -> int:
        """Estimate potential liability amount"""
        base_amounts = {
            'Low': (500000, 5000000),
            'Medium': (5000000, 50000000),
            'High': (50000000, 500000000)
        }

        min_amt, max_amt = base_amounts[severity]
        return random.randint(min_amt, max_amt)

    async def store_legal_data_in_neo4j(
        self,
        ticker: str,
        company_name: str,
        company_data: Dict[str, Any]
    ):
        """Store all legal data in Neo4j graph database"""
        try:
            # Ensure Neo4j is connected
            if not neo4j_manager.driver:
                await neo4j_manager.connect()

            # Create company node
            await neo4j_manager.create_company_node(company_data)

            # Generate and store lawsuits
            lawsuits = self.generate_lawsuits(ticker, company_name, count=3)
            for lawsuit in lawsuits:
                await neo4j_manager.create_lawsuit_node(ticker, lawsuit)

            # Generate and store subsidiaries
            subsidiaries = self.generate_subsidiaries(ticker, company_name, count=2)
            for subsidiary in subsidiaries:
                await neo4j_manager.create_subsidiary_relationship(ticker, subsidiary['name'])

            # Generate and store executives
            executives = self.generate_executive_connections(ticker, company_name)
            for executive in executives:
                await neo4j_manager.create_executive_node(ticker, executive)

            # Generate and store regulatory actions
            actions = self.generate_regulatory_actions(ticker, company_name, count=2)
            for action in actions:
                await neo4j_manager.create_regulatory_action_node(ticker, action)

            logger.info(f"Stored complete legal graph for {ticker} in Neo4j")

            return {
                'lawsuits': len(lawsuits),
                'subsidiaries': len(subsidiaries),
                'executives': len(executives),
                'regulatory_actions': len(actions)
            }

        except Exception as e:
            logger.error(f"Error storing legal data in Neo4j for {ticker}: {e}")
            return None


# Global instance
legal_data_service = LegalDataService()
