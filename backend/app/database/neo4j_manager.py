"""
Neo4j Graph Database Manager
Manages knowledge graph for entity relationships
"""

from neo4j import GraphDatabase, AsyncGraphDatabase
from typing import List, Dict, Any, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jManager:
    """Manages Neo4j graph database operations"""

    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE
        self.driver = None

    async def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j")
            await self.create_constraints()
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")

    async def create_constraints(self):
        """Create constraints and indices"""
        constraints = [
            "CREATE CONSTRAINT company_ticker IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE",
            "CREATE CONSTRAINT executive_id IF NOT EXISTS FOR (e:Executive) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT lawsuit_id IF NOT EXISTS FOR (l:Lawsuit) REQUIRE l.id IS UNIQUE",
        ]

        with self.driver.session(database=self.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {e}")

    # Node creation
    async def create_company_node(self, company_data: Dict[str, Any]):
        """Create or update company node"""
        query = """
        MERGE (c:Company {ticker: $ticker})
        SET c.name = $name,
            c.sector = $sector,
            c.industry = $industry,
            c.market_cap = $market_cap
        RETURN c
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, **company_data)
            logger.info(f"Created/updated company node: {company_data['ticker']}")

    async def create_subsidiary_relationship(self, parent_ticker: str, subsidiary_name: str):
        """Create subsidiary relationship"""
        query = """
        MATCH (parent:Company {ticker: $parent_ticker})
        MERGE (sub:Subsidiary {name: $subsidiary_name})
        MERGE (parent)-[:HAS_SUBSIDIARY]->(sub)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, parent_ticker=parent_ticker, subsidiary_name=subsidiary_name)

    async def create_lawsuit_node(self, company_ticker: str, lawsuit_data: Dict[str, Any]):
        """Create lawsuit node and relationship"""
        query = """
        MATCH (c:Company {ticker: $ticker})
        CREATE (l:Lawsuit {
            id: $id,
            title: $title,
            date: $date,
            status: $status,
            description: $description
        })
        CREATE (c)-[:INVOLVED_IN]->(l)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, ticker=company_ticker, **lawsuit_data)

    # Query operations
    async def get_company_graph(self, ticker: str, depth: int = 2) -> Dict[str, Any]:
        """Get company and its relationships"""
        query = f"""
        MATCH path = (c:Company {{ticker: $ticker}})-[*1..{depth}]-(n)
        RETURN c, relationships(path) as rels, collect(n) as nodes
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, ticker=ticker)
            record = result.single()

            if not record:
                return {"nodes": [], "relationships": []}

            # Format for visualization
            return self._format_graph_data(record)

    def _format_graph_data(self, record) -> Dict[str, Any]:
        """Format Neo4j result for frontend visualization"""
        nodes = []
        relationships = []

        # Add main company node
        company = record['c']
        nodes.append({
            'id': company['ticker'],
            'label': company['name'],
            'type': 'Company',
            'properties': dict(company)
        })

        # Add related nodes
        for node in record['nodes']:
            nodes.append({
                'id': node.element_id,
                'label': node.get('name', node.get('title', 'Unknown')),
                'type': list(node.labels)[0] if node.labels else 'Unknown',
                'properties': dict(node)
            })

        # Add relationships
        for rel in record.get('rels', []):
            relationships.append({
                'source': rel.start_node.element_id,
                'target': rel.end_node.element_id,
                'type': rel.type
            })

        return {"nodes": nodes, "relationships": relationships}


# Global instance
neo4j_manager = Neo4jManager()
