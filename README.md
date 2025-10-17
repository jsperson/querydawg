# DataPrism: Natural Language Semantic Layer for Text-to-SQL

A cloud-native text-to-SQL system that uses natural language semantic layers to improve SQL query generation accuracy.

## Overview

DataPrism augments traditional text-to-SQL systems with LLM-generated natural language documentation that describes databases in business terms. This semantic layer includes column purposes, synonyms, relationships, and common query patterns, enabling more accurate SQL generation from natural language questions.

## Key Features

- **Natural Language Semantic Layers**: Automatically generated business-context documentation for databases
- **Dual-Mode Operation**: Compare baseline (schema-only) vs enhanced (with semantic layer) performance
- **Spider Benchmark Evaluation**: Rigorous testing on the industry-standard Spider 1.0 dataset
- **Cloud-Native Architecture**: Deployed on Vercel (frontend) and Railway (backend)
- **Vector Search**: Pinecone-powered semantic retrieval for relevant context

## Expected Results

- 15-25% accuracy improvement over schema-only approaches
- Support for 15-20 Spider benchmark databases
- Production-ready cloud deployment
- Comprehensive evaluation metrics and analysis

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 14, TypeScript, Vercel |
| Backend | FastAPI, Python 3.11+, Railway |
| Vector DB | Pinecone |
| SQL Database | Supabase PostgreSQL |
| LLM | OpenAI GPT-4o / GPT-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VERCEL (Frontend)                     │
│               Next.js 14 + TypeScript                    │
│  - Query interface                                       │
│  - Comparison dashboard                                  │
│  - Evaluation results viewer                            │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS REST API
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  RAILWAY (Backend)                       │
│                  FastAPI (Python)                        │
│  - Schema extraction                                     │
│  - Semantic layer generation                            │
│  - Context retrieval                                    │
│  - Text-to-SQL generation                               │
│  - SQL execution                                        │
└───┬──────────────┬──────────────┬──────────────┬────────┘
    │              │              │              │
    ↓              ↓              ↓              ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ OpenAI   │  │Pinecone  │  │Supabase  │  │Supabase  │
│   API    │  │ Vectors  │  │PostgreSQL│  │ Tables   │
│          │  │          │  │          │  │          │
│GPT-4o    │  │Semantic  │  │Spider    │  │Semantic  │
│4o-mini   │  │Metadata  │  │Databases │  │Docs      │
│Embeddings│  │Search    │  │          │  │Eval Data │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- Accounts for: Vercel, Railway, Supabase, Pinecone

### Installation

1. Clone the repository:
```bash
git clone https://github.com/[username]/dataprism.git
cd dataprism
```

2. Set up backend:
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

3. Set up frontend:
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your API endpoints
```

4. Load Spider databases into Supabase (see docs/SETUP.md for details)

5. Generate semantic layers:
```bash
python scripts/generate_semantic_layers.py
```

6. Run locally:
```bash
# Backend
uvicorn app.main:app --reload

# Frontend (new terminal)
npm run dev
```

## Project Structure

```
dataprism/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── data/            # Spider dataset
├── docs/            # Documentation
├── evaluation/      # Evaluation scripts and results
├── scripts/         # Utility scripts
└── README.md
```

## Development Timeline

- **Week 1**: Foundation & baseline system deployment
- **Week 2**: Semantic layer generation for all databases
- **Week 3**: Vector search and context retrieval implementation
- **Week 4**: Enhanced text-to-SQL with semantic integration
- **Week 5**: SQL execution engine and comparison mode
- **Week 6**: Comprehensive evaluation on Spider benchmark
- **Week 7**: Documentation, presentation, and open-source release


## Evaluation Metrics

- **Primary Metric**: Execution accuracy (% of queries returning correct results)
- **Target Performance**: 60-75% accuracy with semantic layer vs 40-50% baseline
- **Test Set**: 200-300 questions from Spider dev.json
- **Comparison**: Baseline (schema-only) vs Enhanced (with semantic layer)

## API Endpoints

```
POST /api/schema/extract       - Extract database schema
POST /api/semantic/generate    - Generate semantic layer
POST /api/semantic/retrieve    - Retrieve relevant context
POST /api/sql/baseline         - Generate SQL (baseline)
POST /api/sql/enhanced         - Generate SQL (with semantic layer)
POST /api/sql/execute          - Execute SQL query
POST /api/sql/compare          - Compare systems
GET  /api/databases            - List available databases
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Research Context

This project is an independent study for the Master of Science in Data Science program at Newman University, investigating whether natural language semantic layers improve text-to-SQL accuracy compared to schema-only approaches.

## References

### Key Papers
- Yu et al. (2018). [Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task](https://arxiv.org/abs/1809.08887)
- Lei et al. (2024). [Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows](https://arxiv.org/abs/2411.07763)

### Resources
- [Spider 1.0 Dataset](https://yale-lily.github.io/spider)
- [Spider GitHub Repository](https://github.com/taoyds/spider)

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Author

Jason "Scott" Person
Newman University
Master of Science in Data Science
