# MarketMoves Setup Guide

## Complete Setup Instructions

Follow these steps to get MarketMoves running on your machine.

### 1. Install System Requirements

#### Install Python 3.10+
```bash
# macOS (with Homebrew)
brew install python@3.10

# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv

# Verify installation
python3 --version
```

#### Install Node.js 18+
```bash
# macOS (with Homebrew)
brew install node

# Ubuntu/Debian (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

#### Install Docker
```bash
# macOS
# Download from: https://www.docker.com/products/docker-desktop

# Ubuntu
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version
docker-compose --version
```

### 2. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version

# Pull the LLM model (choose one)
ollama pull llama3.1  # Recommended, ~4.7GB
# OR
ollama pull mistral   # Alternative, ~4.1GB

# Start Ollama server (if not auto-started)
ollama serve
```

### 3. Clone and Setup Project

```bash
# Navigate to your projects directory
cd ~/Documents/Courses&Projects/Projects/MarketMoves

# The project structure is already created, let's set it up
```

### 4. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use any text editor
```

#### Configure .env File

Edit the `.env` file and update:

```bash
# REQUIRED: Add your email for SEC Edgar
SEC_EDGAR_USER_AGENT=MarketMoves your-email@example.com

# OPTIONAL: Add NewsAPI key (get free key from newsapi.org)
NEWSAPI_KEY=your_newsapi_key_here

# Other settings use defaults
```

### 5. Start Neo4j Database

```bash
# From project root directory
cd ..  # Back to MarketMoves root

# Start Neo4j with Docker Compose
docker-compose up -d

# Verify Neo4j is running
docker ps

# Access Neo4j Browser (optional)
# Open http://localhost:7474 in your browser
# Username: neo4j
# Password: marketmoves
```

### 6. Initialize Backend

```bash
# Go back to backend directory
cd backend

# Make sure virtual environment is activated
source venv/bin/activate

# Start the FastAPI server
python -m app.main

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Leave this terminal running!**

### 7. Frontend Setup

Open a **new terminal window**:

```bash
# Navigate to frontend directory
cd ~/Documents/Courses&Projects/Projects/MarketMoves/frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev

# You should see:
# VITE ready in XXX ms
# Local: http://localhost:5173
```

**Leave this terminal running!**

### 8. Access the Application

Open your web browser and navigate to:

```
http://localhost:5173
```

You should see the MarketMoves dashboard!

## Initial Data Setup

### Option 1: Using Python Script

In a **new terminal** (with backend venv activated):

```python
# Run Python script to load demo data
cd backend
source venv/bin/activate

python << EOF
import asyncio
from app.services.data_ingestion.yahoo_finance import yahoo_finance
from app.database.sqlite_manager import db_manager

async def init_data():
    await db_manager.init_database()
    await yahoo_finance.initialize_demo_data()

asyncio.run(init_data())
EOF
```

### Option 2: Using API Endpoints

```bash
# Fetch data for specific tickers
curl -X POST http://localhost:8000/api/v1/market/stocks/AAPL/update
curl -X POST http://localhost:8000/api/v1/market/stocks/MSFT/update
curl -X POST http://localhost:8000/api/v1/market/stocks/GOOGL/update
```

## Verification Checklist

- [ ] Backend API running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] Neo4j running on http://localhost:7474
- [ ] Ollama service running (check with `ollama list`)
- [ ] Can access http://localhost:8000/docs (API documentation)
- [ ] Can access http://localhost:5173 (Dashboard)
- [ ] Can see companies in the dashboard dropdown

## Common Issues & Solutions

### Issue: "Module not found" error

**Solution:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Connection refused" to Ollama

**Solution:**
```bash
# Start Ollama server
ollama serve

# In another terminal, verify
curl http://localhost:11434/api/tags
```

### Issue: Neo4j won't start

**Solution:**
```bash
# Stop and remove containers
docker-compose down

# Start fresh
docker-compose up -d

# Check logs
docker logs marketmoves-neo4j
```

### Issue: Port already in use

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in backend/app/main.py
```

### Issue: Frontend won't compile

**Solution:**
```bash
cd frontend

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm cache clean --force
npm install
```

## Next Steps

Once everything is running:

1. **Explore the Dashboard**: Select different companies from the dropdown
2. **Calculate Risk Scores**: Click on companies to see risk analysis
3. **Generate AI Stories**: Use the "Generate" button in the Risk Stories panel
4. **Check API Docs**: Visit http://localhost:8000/docs to explore API endpoints
5. **Add More Companies**: Use the update endpoint to add more stock tickers

## Development Tips

### Adding New Companies

```bash
curl -X POST http://localhost:8000/api/v1/market/stocks/TSLA/update
curl -X POST http://localhost:8000/api/v1/market/stocks/NVDA/update
```

### Viewing Logs

```bash
# Backend logs
# Check the terminal where backend is running

# Neo4j logs
docker logs marketmoves-neo4j

# Frontend logs
# Check the terminal where frontend is running
```

### Stopping Services

```bash
# Stop backend: Ctrl+C in backend terminal
# Stop frontend: Ctrl+C in frontend terminal

# Stop Neo4j
docker-compose down
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the logs in each terminal
3. Ensure all prerequisites are properly installed
4. Verify network connectivity and ports are not blocked

Happy analyzing! 📊
