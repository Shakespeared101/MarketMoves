# MarketMoves: Interactive Market Anomaly & Risk Intelligence Dashboard

A comprehensive data visualization and risk intelligence platform that combines financial data analysis, machine learning, and interactive visualizations to provide insights into market risks, anomalies, and corporate intelligence.

![Tech Stack](https://img.shields.io/badge/Backend-FastAPI-009688)
![Tech Stack](https://img.shields.io/badge/Frontend-React-61DAFB)
![Tech Stack](https://img.shields.io/badge/Database-SQLite%20%2B%20DuckDB-003B57)
![Tech Stack](https://img.shields.io/badge/Graph-Neo4j-008CC1)
![Tech Stack](https://img.shields.io/badge/LLM-Ollama-000000)

## Features

### Core Capabilities
- **Multi-Factor Risk Scoring**: Combines volatility, sentiment, litigation, financial anomalies, and regulatory factors
- **Real-Time Market Data**: Integration with Yahoo Finance for live stock prices and company information
- **SEC Filings Analysis**: Automated extraction and analysis of 10-K filings from SEC Edgar
- **News Sentiment Analysis**: Aggregates corporate news with VADER sentiment analysis
- **LLM-Powered Insights**: Uses Ollama (Llama 3.1/Mistral) for generating risk narratives
- **Knowledge Graph**: Neo4j-based entity relationships (companies, subsidiaries, lawsuits, regulators)
- **RAG (Retrieval-Augmented Generation)**: Document Q&A with SEC filings
- **Interactive Visualizations**: Risk timelines, heatmaps, correlation matrices, and graph visualizations

### Technical Highlights
- **Backend**: FastAPI with async support
- **Databases**:
  - SQLite for transactional data
  - DuckDB for columnar analytics
  - Neo4j for knowledge graph
  - ChromaDB for vector embeddings
- **Frontend**: React with Vite, TailwindCSS, Recharts, D3.js
- **ML/AI**: Sentence Transformers for embeddings, VADER for sentiment, Ollama for LLM

## Project Structure

```
MarketMoves/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application
│   │   ├── config.py                # Configuration
│   │   ├── api/routes/              # API endpoints
│   │   │   ├── market_data.py
│   │   │   ├── risk_analysis.py
│   │   │   └── insights.py
│   │   ├── services/
│   │   │   ├── data_ingestion/      # Data fetchers
│   │   │   ├── risk_engine.py       # Risk scoring
│   │   │   └── rag_service.py       # RAG implementation
│   │   ├── database/                # Database managers
│   │   └── utils/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/              # React components
│   │   ├── services/api.js          # API client
│   │   └── main.jsx
│   └── package.json
├── data/                            # Local data storage
├── docker-compose.yml               # Neo4j setup
└── README.md

```

## Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (for Neo4j)
- Ollama (for LLM inference)

### Step 1: Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull llama3.1
# or
ollama pull mistral
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your configuration:
# - SEC_EDGAR_USER_AGENT: Your email for SEC API
# - NEWSAPI_KEY: Get free key from https://newsapi.org/
```

### Step 3: Start Neo4j

```bash
# From project root
docker-compose up -d

# Verify Neo4j is running
# Open http://localhost:7474 in browser
# Login: neo4j / marketmoves
```

### Step 4: Initialize Database

```bash
cd backend

# Run FastAPI server
python -m app.main

# In another terminal, initialize demo data:
# This will fetch data for popular stocks
curl -X POST http://localhost:8000/api/v1/market/initialize
```

### Step 5: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:5173
```

## Running the Application

### Terminal 1: Backend API
```bash
cd backend
source venv/bin/activate
python -m app.main
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

### Terminal 3: Ollama (if not running as service)
```bash
ollama serve
```

## API Endpoints

### Market Data
- `GET /api/v1/market/companies` - List all tracked companies
- `GET /api/v1/market/companies/{ticker}` - Get company details
- `GET /api/v1/market/stocks/{ticker}/prices` - Get stock prices
- `GET /api/v1/market/stocks/{ticker}/latest` - Get latest price
- `POST /api/v1/market/stocks/{ticker}/update` - Update ticker data

### Risk Analysis
- `GET /api/v1/risk/{ticker}` - Get current risk score
- `GET /api/v1/risk/{ticker}/timeline` - Get risk timeline
- `POST /api/v1/risk/calculate` - Calculate risk for multiple tickers

### LLM Insights
- `POST /api/v1/insights/query` - Query documents using RAG
- `POST /api/v1/insights/risk-story` - Generate risk narrative

## Usage Examples

### Fetching Market Data

```python
import asyncio
from app.services.data_ingestion.yahoo_finance import yahoo_finance

# Fetch company info and prices
async def main():
    await yahoo_finance.fetch_company_info('AAPL')
    prices = await yahoo_finance.fetch_historical_prices('AAPL', period='1y')
    print(f"Fetched {len(prices)} price records")

asyncio.run(main())
```

### Calculating Risk Score

```python
from app.services.risk_engine import risk_engine

# Calculate comprehensive risk score
risk_data = await risk_engine.calculate_overall_risk('AAPL')
print(f"Risk Score: {risk_data['overall_risk_score']}")
print(f"Risk Level: {risk_data['risk_level']}")
```

### Generating LLM Insights

```bash
curl -X POST http://localhost:8000/api/v1/insights/risk-story \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

## Data Sources

### Available Data Sources
1. **Yahoo Finance** (Free, No API Key)
   - Stock prices, company info, financial metrics
   - Real-time and historical data

2. **SEC Edgar** (Free, No API Key)
   - 10-K, 10-Q, 8-K filings
   - Requires user-agent with email

3. **NewsAPI** (Free Tier)
   - Corporate news articles
   - Get free key: https://newsapi.org/

### Adding New Companies

```python
from app.services.data_ingestion.yahoo_finance import yahoo_finance

# Add a new company to track
tickers = ['MSFT', 'GOOGL', 'AMZN']
await yahoo_finance.fetch_multiple_tickers(tickers, period='2y')
```

## Risk Scoring Formula

The overall risk score is calculated using weighted components:

```
Risk Score = (
    0.30 × Volatility Score +
    0.25 × Litigation Score +
    0.20 × Sentiment Score +
    0.15 × Financial Anomaly Score +
    0.10 × Regulatory Score
)
```

### Risk Levels
- **0-3**: Low Risk (Green)
- **3-6**: Medium Risk (Yellow)
- **6-8**: High Risk (Orange)
- **8-10**: Critical Risk (Red)

## Architecture

### Backend Architecture
```
API Layer (FastAPI)
    ↓
Service Layer (Business Logic)
    ├── Data Ingestion Services
    ├── Risk Engine
    ├── RAG Service
    └── Graph Builder
    ↓
Data Layer
    ├── SQLite (Transactional)
    ├── DuckDB (Analytics)
    ├── Neo4j (Graph)
    └── ChromaDB (Vectors)
```

### Frontend Architecture
```
React Components
    ↓
React Query (State Management)
    ↓
Axios (API Client)
    ↓
FastAPI Backend
```

## Development Roadmap

### Phase 1: Foundation ✅
- [x] Backend API with FastAPI
- [x] Database setup (SQLite, DuckDB)
- [x] Yahoo Finance integration
- [x] Basic risk scoring

### Phase 2: Intelligence ✅
- [x] LLM integration with Ollama
- [x] RAG service for document Q&A
- [x] SEC Edgar integration
- [x] News sentiment analysis

### Phase 3: Knowledge Graph ✅
- [x] Neo4j setup
- [x] Entity relationship modeling
- [x] Graph queries

### Phase 4: Visualization ✅
- [x] React frontend with Vite
- [x] Risk timeline chart
- [x] Dashboard layout
- [x] LLM-powered risk stories

### Phase 5: Advanced Features 🚧
- [ ] RAPTOR hierarchical retrieval
- [ ] M&A cluster graph visualization
- [ ] Volatility heatmap
- [ ] Correlation matrix
- [ ] Entity explorer with force-directed graph
- [ ] Scheduled data updates (Celery)
- [ ] Real-time streaming data
- [ ] Advanced anomaly detection

## Performance Optimization

### Backend
- Uses DuckDB for fast columnar analytics
- Async database operations with aiosqlite
- Connection pooling for Neo4j
- Vector similarity search with ChromaDB

### Frontend
- React Query for caching and data synchronization
- Lazy loading of components
- Debounced API calls
- Optimized re-renders

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### Neo4j Connection Issues
```bash
# Check Neo4j status
docker ps | grep neo4j

# Restart Neo4j
docker-compose restart neo4j

# View logs
docker logs marketmoves-neo4j
```

### Database Initialization Issues
```bash
# Reset databases
rm data/marketmoves.db
rm data/analytics.duckdb

# Re-run initialization
python -m app.main
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Yahoo Finance for free market data API
- SEC for public filings access
- Anthropic/Meta for open-source LLMs
- The open-source community

## Contact

For questions or support, please open an issue on GitHub.

---

Built with ❤️ for financial risk intelligence and data storytelling
