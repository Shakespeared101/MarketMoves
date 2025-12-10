# MarketMoves - Quick Start Guide

Get MarketMoves running in under 10 minutes!

## Prerequisites Check

```bash
# Check Python (need 3.10+)
python3 --version

# Check Node.js (need 18+)
node --version

# Check Docker (need any recent version)
docker --version
```

If any are missing, see [SETUP.md](SETUP.md) for installation instructions.

## 5-Minute Setup

### Step 1: Install Ollama (2 min)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull LLM model (runs in background)
ollama pull llama3.1 &
```

### Step 2: Backend Setup (2 min)

```bash
cd backend

# Create virtual environment and install
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: Add your email to SEC_EDGAR_USER_AGENT line
```

### Step 3: Start Services (1 min)

```bash
# Start Neo4j (from project root)
cd ..
docker-compose up -d

# Start backend (from backend directory)
cd backend
python -m app.main &
```

### Step 4: Frontend Setup (2 min)

```bash
# In a new terminal
cd frontend
npm install
npm run dev
```

### Step 5: Load Demo Data (2 min)

```bash
# In a new terminal
cd backend
source venv/bin/activate
python init_demo_data.py
```

## Access the Application

Open your browser to: **http://localhost:5173**

## What to Try First

1. **Select a company** from the dropdown (e.g., AAPL, MSFT, GOOGL)
2. **View the risk score** and component breakdown
3. **Check the risk timeline** chart
4. **Click "Generate"** in Risk Stories to create an AI narrative

## Quick Commands Reference

### Start Everything
```bash
# Terminal 1: Neo4j
docker-compose up -d

# Terminal 2: Backend
cd backend && source venv/bin/activate && python -m app.main

# Terminal 3: Frontend
cd frontend && npm run dev

# Terminal 4: Ollama (if not auto-running)
ollama serve
```

### Stop Everything
```bash
# Stop backend: Ctrl+C in Terminal 2
# Stop frontend: Ctrl+C in Terminal 3
# Stop Neo4j:
docker-compose down
```

### Add More Companies
```bash
curl -X POST http://localhost:8000/api/v1/market/stocks/TSLA/update
curl -X POST http://localhost:8000/api/v1/market/stocks/NVDA/update
```

## Verify Installation

Check these URLs work:
- ✅ Frontend: http://localhost:5173
- ✅ Backend API: http://localhost:8000/docs
- ✅ Health Check: http://localhost:8000/health
- ✅ Neo4j: http://localhost:7474 (neo4j/marketmoves)

## Common Issues

**Ollama not responding?**
```bash
ollama serve
# In another terminal: ollama list
```

**Port 8000 in use?**
```bash
# Kill process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

**No data showing?**
```bash
# Re-run initialization
cd backend && python init_demo_data.py
```

## Need Help?

- Full setup guide: [SETUP.md](SETUP.md)
- Project documentation: [README.md](README.md)
- API docs: http://localhost:8000/docs (when running)

## Next Steps

Once everything works:
1. Explore different companies
2. Try the risk story generator
3. Check out the API documentation
4. Modify the code to add features
5. Deploy to production

Happy analyzing! 🚀
