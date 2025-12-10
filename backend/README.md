# MarketMoves Backend API

FastAPI-based backend for the MarketMoves risk intelligence platform.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Start the server
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, access:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration management
├── api/
│   └── routes/             # API endpoint definitions
│       ├── market_data.py  # Stock market data endpoints
│       ├── risk_analysis.py # Risk scoring endpoints
│       └── insights.py      # LLM insights endpoints
├── services/
│   ├── data_ingestion/     # External data fetchers
│   │   ├── yahoo_finance.py
│   │   ├── sec_edgar.py
│   │   └── news_fetcher.py
│   ├── risk_engine.py      # Risk scoring logic
│   └── rag_service.py      # RAG implementation
├── database/               # Database managers
│   ├── sqlite_manager.py   # SQLite operations
│   ├── duckdb_analytics.py # DuckDB analytics
│   └── neo4j_manager.py    # Neo4j graph operations
└── utils/
    └── llm_client.py       # Ollama LLM client
```

## Environment Variables

Key configuration in `.env`:

```bash
# Database Paths
SQLITE_DB_PATH=./data/marketmoves.db
DUCKDB_PATH=./data/analytics.duckdb

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=marketmoves

# Ollama LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# API Keys
SEC_EDGAR_USER_AGENT=MarketMoves your-email@example.com
NEWSAPI_KEY=your_key_here
```

## Dependencies

Core dependencies:
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **SQLite/aiosqlite**: Primary database
- **DuckDB**: Analytics database
- **Neo4j**: Graph database
- **Ollama**: LLM client
- **yfinance**: Yahoo Finance data
- **pandas**: Data manipulation
- **sentence-transformers**: Embeddings
- **chromadb**: Vector database
- **langchain**: LLM orchestration

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Development

```bash
# Run in development mode with auto-reload
uvicorn app.main:app --reload

# Format code
black app/
isort app/

# Lint
flake8 app/
pylint app/
```

## API Examples

### Get Company Risk Score
```bash
curl http://localhost:8000/api/v1/risk/AAPL
```

### Generate Risk Story
```bash
curl -X POST http://localhost:8000/api/v1/insights/risk-story \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

### Update Stock Data
```bash
curl -X POST http://localhost:8000/api/v1/market/stocks/AAPL/update
```

## Database Schema

### Companies
- ticker, name, sector, industry, market_cap

### Stock Prices
- ticker, date, open, high, low, close, volume

### Risk Scores
- ticker, date, overall_risk_score, component_scores

### News Articles
- ticker, headline, content, sentiment_score

### SEC Filings
- ticker, filing_type, filing_date, content, risk_factors

## Performance Tips

1. **Use DuckDB for analytics**: Columnar storage for fast aggregations
2. **Index frequently queried fields**: ticker, date
3. **Cache API responses**: Implement caching layer
4. **Batch operations**: Use bulk inserts for data ingestion
5. **Connection pooling**: Reuse database connections

## Troubleshooting

### Database locked error
```python
# Increase timeout in config
SQLITE_TIMEOUT = 30000
```

### Ollama connection failed
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Pull model if missing
ollama pull llama3.1
```

### Import errors
```bash
# Ensure you're in the correct directory
cd backend
python -m app.main
```
