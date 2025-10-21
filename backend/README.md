# Backend - FastAPI Application

This directory contains the DataPrism backend API built with FastAPI.

## Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── routers/             # API endpoints
│   │   ├── schema.py        # Schema extraction
│   │   ├── semantic.py      # Semantic layer generation/retrieval
│   │   ├── sql.py           # Text-to-SQL generation
│   │   └── evaluate.py      # Evaluation endpoints
│   ├── services/            # Core business logic
│   │   ├── openai_service.py    # OpenAI API integration
│   │   ├── pinecone_service.py  # Vector search
│   │   ├── supabase_service.py  # Database operations
│   │   └── generator.py         # Semantic layer generation
│   └── models/              # Pydantic models
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in git)
└── Dockerfile              # (Optional) Container configuration
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

### Database
- `GET /api/databases` - List available Spider databases (requires X-API-Key)

### Coming Soon
- `GET /api/schema/{database}` - Get database schema
- `POST /api/text-to-sql/baseline` - Generate SQL (baseline)
- `POST /api/text-to-sql/enhanced` - Generate SQL (enhanced with semantic layer)
- `POST /api/execute` - Execute SQL query

## Authentication

All endpoints (except `/api/health`) require API key authentication:

```bash
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:8000/api/databases
```

Set `API_KEY` in your `.env` file.

## Deployment

### Railway (Production)

Deployed to Railway automatically when pushed to GitHub (main branch).

**Configuration**:
- `railway.toml` - Deployment configuration
- `.railwayignore` - Files to exclude from deployment

**Setup Railway**:
1. See [DEPLOYMENT.md](../DEPLOYMENT.md) for complete setup guide
2. Connect GitHub repository to Railway
3. Configure environment variables in Railway dashboard
4. Railway will auto-deploy on push to `main`

**Railway URL**: `https://your-project.up.railway.app`
