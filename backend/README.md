# Backend - FastAPI Application

This directory contains the QueryDawg backend API built with FastAPI.

**Status:** Week 1 Complete - Baseline text-to-SQL system functional

## Architecture

The backend uses a **modular LLM architecture** that supports multiple AI providers through a common interface, making it easy to switch between OpenAI, Anthropic, Ollama, or add new providers.

## Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Environment configuration management
│   ├── llm/                       # Modular LLM architecture
│   │   ├── base.py                # Base LLM interface (ABC)
│   │   ├── openai_llm.py          # OpenAI GPT-4 implementation
│   │   ├── anthropic_llm.py       # Anthropic Claude implementation
│   │   └── ollama_llm.py          # Ollama local LLM implementation
│   ├── database/                  # Database operations
│   │   ├── schema_extractor.py    # Extract schema from SQLite DBs
│   │   └── sql_executor.py        # Safe SQL execution with limits
│   └── routers/                   # API endpoints
│       ├── databases.py           # List available databases
│       ├── schema.py              # Get database schema
│       ├── text_to_sql.py         # Generate SQL from natural language
│       └── execute.py             # Execute SQL queries
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables (not in git)
├── railway.toml                   # Railway deployment config
└── .railwayignore                # Railway deployment exclusions
```

## Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp ../.env.example .env
# Edit .env with your actual API keys
```

4. Run development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### System
- `GET /api/health` - Health check (no auth required)
- `GET /` - Root endpoint with API info

### Database Operations
- `GET /api/databases` - List available Spider databases
- `GET /api/schema/{database}` - Get detailed schema for a database (tables, columns, foreign keys, row counts)

### Text-to-SQL Generation
- `POST /api/text-to-sql/baseline` - Generate SQL from natural language (schema-only, no semantic layer)
  - Request: `{"question": "...", "database": "..."}`
  - Response: SQL, explanation, metadata (tokens, cost, generation time)

### Query Execution
- `POST /api/execute` - Execute SQL query with safety limits
  - Request: `{"sql": "...", "database": "..."}`
  - Response: Results, column names, row count, execution time
  - Safety: Read-only, 1000 row limit, 30 second timeout

### Planned (Week 2+)
- `POST /api/text-to-sql/enhanced` - Generate SQL with semantic layer enhancement
- `POST /api/semantic/generate` - Generate semantic layer for a database
- `GET /api/semantic/{database}` - Retrieve semantic layer documentation

## Authentication

All endpoints (except `/api/health`) require API key authentication:

```bash
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:8000/api/databases
```

Set `API_KEY` in your `.env` file.

## Deployment

### Railway (Production-Ready)

The backend is configured for Railway deployment and can be activated on-demand.

**Configuration Files**:
- `railway.toml` - Deployment configuration
- `.railwayignore` - Files to exclude from deployment
- Environment variables configured in Railway dashboard

**Setup**:
1. See [DEPLOYMENT.md](../DEPLOYMENT.md) for complete deployment guide
2. Railway project: `querydawg-production`
3. Auto-deploys from GitHub `main` branch when active
4. Cold start: ~3 seconds for first request after idle

**Production URL** (when active): `https://querydawg-production.up.railway.app`

**Key Features**:
- Automatic HTTPS
- Environment variable management
- GitHub integration for CI/CD
- Health check monitoring at `/api/health`
- API documentation at `/docs` and `/redoc`

### Local Development

For local testing, databases are stored in `../data/spider/database/` as SQLite files. The application automatically detects and loads all `.sqlite` files from this directory.
