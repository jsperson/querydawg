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

## Deployment

Deployed to Railway automatically when pushed to GitHub (main branch).

Railway configuration: See `railway.toml` in project root.
