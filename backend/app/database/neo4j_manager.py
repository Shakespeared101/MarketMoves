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
        MATCH (c:Company {ticker: $company_ticker})
        CREATE (l:Lawsuit {
            id: $id,
            title: $title,
            lawsuit_type: $lawsuit_type,
            filed_date: $filed_date,
            status: $status,
            severity: $severity,
            impact_score: $impact_score,
            description: $description
        })
        CREATE (c)-[:INVOLVED_IN]->(l)
        """

        # Remove ticker from lawsuit_data to avoid conflicts
        data = {k: v for k, v in lawsuit_data.items() if k != 'ticker' and k != 'company_name'}

        with self.driver.session(database=self.database) as session:
            session.run(query, company_ticker=company_ticker, **data)

    async def create_executive_node(self, company_ticker: str, executive_data: Dict[str, Any]):
        """Create executive node and relationship"""
        query = """
        MATCH (c:Company {ticker: $company_ticker})
        MERGE (e:Executive {id: $id})
        SET e.name = $name,
            e.position = $position,
            e.tenure_years = $tenure_years,
            e.background = $background
        MERGE (e)-[:WORKS_AT]->(c)
        """

        # Remove ticker/company fields to avoid conflicts
        data = {k: v for k, v in executive_data.items() if k not in ['company_ticker', 'company_name']}

        with self.driver.session(database=self.database) as session:
            session.run(query, company_ticker=company_ticker, **data)

    async def create_regulatory_action_node(self, company_ticker: str, action_data: Dict[str, Any]):
        """Create regulatory action node and relationship"""
        query = """
        MATCH (c:Company {ticker: $company_ticker})
        CREATE (r:RegulatoryAction {
            id: $id,
            agency: $agency,
            action_type: $action_type,
            date: $date,
            severity: $severity,
            description: $description,
            status: $status
        })
        CREATE (c)-[:SUBJECT_TO]->(r)
        """

        # Remove ticker/company fields to avoid conflicts
        data = {k: v for k, v in action_data.items() if k not in ['ticker', 'company_name']}

        with self.driver.session(database=self.database) as session:
            session.run(query, company_ticker=company_ticker, **data)

    # Query operations
    async def get_company_graph(self, ticker: str, depth: int = 2) -> Dict[str, Any]:
        """Get company and its relationships for visualization"""
        query = f"""
        MATCH (c:Company {{ticker: $ticker}})
        OPTIONAL MATCH (c)-[r1]-(n)
        WITH c, collect({{node: n, rel: r1, relType: type(r1)}}) as connections
        RETURN c, connections
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, ticker=ticker)
            record = result.single()

            if not record:
                return {"nodes": [], "edges": []}

            # Format for visualization
            return self._format_graph_data_for_viz(record, ticker)

    async def get_lawsuits_for_risk(self, ticker: str) -> Dict[str, Any]:
        """Get lawsuit count and severity for risk scoring"""
        query = """
        MATCH (c:Company {ticker: $ticker})-[:INVOLVED_IN]->(l:Lawsuit)
        WHERE l.status IN ['Filed', 'In Litigation', 'Active']
        RETURN
            count(l) as lawsuit_count,
            avg(l.impact_score) as avg_impact,
            collect({
                severity: l.severity,
                impact: l.impact_score,
                type: l.lawsuit_type
            }) as lawsuits
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, ticker=ticker)
            record = result.single()

            if not record or record['lawsuit_count'] == 0:
                return {
                    'lawsuit_count': 0,
                    'avg_impact': 0.0,
                    'high_severity_count': 0,
                    'total_impact': 0.0
                }

            lawsuits = record['lawsuits']
            high_severity = sum(1 for l in lawsuits if l['severity'] == 'High')

            return {
                'lawsuit_count': record['lawsuit_count'],
                'avg_impact': float(record['avg_impact']),
                'high_severity_count': high_severity,
                'total_impact': sum(l['impact'] for l in lawsuits)
            }

    async def get_company_entities(self, ticker: str) -> Dict[str, List]:
        """Get all entities related to a company"""
        queries = {
            'subsidiaries': """
                MATCH (c:Company {ticker: $ticker})-[:HAS_SUBSIDIARY]->(s:Subsidiary)
                RETURN collect(s.name) as items
            """,
            'executives': """
                MATCH (e:Executive)-[:WORKS_AT]->(c:Company {ticker: $ticker})
                RETURN collect({name: e.name, position: e.position}) as items
            """,
            'lawsuits': """
                MATCH (c:Company {ticker: $ticker})-[:INVOLVED_IN]->(l:Lawsuit)
                RETURN collect({title: l.title, status: l.status, severity: l.severity}) as items
            """,
            'regulatory_actions': """
                MATCH (c:Company {ticker: $ticker})-[:SUBJECT_TO]->(r:RegulatoryAction)
                RETURN collect({agency: r.agency, type: r.action_type, status: r.status}) as items
            """
        }

        results = {}
        with self.driver.session(database=self.database) as session:
            for key, query in queries.items():
                result = session.run(query, ticker=ticker)
                record = result.single()
                results[key] = record['items'] if record else []

        return results

    def _format_graph_data_for_viz(self, record, ticker: str) -> Dict[str, Any]:
        """Format Neo4j result for frontend visualization (vis.js/D3 compatible)"""
        nodes = []
        edges = []

        # Add main company node
        company = record['c']
        nodes.append({
            'id': ticker,
            'label': company.get('name', ticker),
            'type': 'Company',
            'group': 'company',
            'properties': dict(company),
            'color': '#4A90E2',
            'size': 30
        })

        # Process connections
        node_id_counter = 1
        for conn in record['connections']:
            if conn['node'] is None:
                continue

            node = conn['node']
            node_labels = list(node.labels) if hasattr(node, 'labels') else []
            node_type = node_labels[0] if node_labels else 'Unknown'

            # Generate unique ID for the node
            node_props = dict(node)
            node_id = node_props.get('id', f"{node_type}_{node_id_counter}")
            node_id_counter += 1

            # Color and size based on type
            color_map = {
                'Lawsuit': '#E74C3C',
                'Executive': '#F39C12',
                'Subsidiary': '#27AE60',
                'RegulatoryAction': '#8E44AD'
            }

            size_map = {
                'Lawsuit': 20,
                'Executive': 15,
                'Subsidiary': 18,
                'RegulatoryAction': 20
            }

            # Get node label
            label = (node_props.get('title') or
                    node_props.get('name') or
                    node_props.get('agency') or
                    node_type)

            nodes.append({
                'id': node_id,
                'label': label,
                'type': node_type,
                'group': node_type.lower(),
                'properties': node_props,
                'color': color_map.get(node_type, '#95A5A6'),
                'size': size_map.get(node_type, 15)
            })

            # Add edge
            rel_type = conn.get('relType', 'RELATED_TO')
            edges.append({
                'id': f"edge_{ticker}_{node_id}",
                'from': ticker,
                'to': node_id,
                'label': rel_type.replace('_', ' '),
                'arrows': 'to',
                'color': '#95A5A6'
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }

    def _format_graph_data(self, record) -> Dict[str, Any]:
        """Legacy format method - kept for compatibility"""
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
        for node in record.get('nodes', []):
            nodes.append({
                'id': node.element_id,
                'label': node.get('name', node.get('title', 'Unknown')),
                'type': list(node.labels)[0] if hasattr(node, 'labels') and node.labels else 'Unknown',
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
