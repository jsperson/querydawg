# QueryDawg: Natural Language Semantic Layer for Text-to-SQL

A cloud-native text-to-SQL system that uses automatically generated natural language semantic layers to improve SQL query generation accuracy.

**📊 Project Status:** ✅ COMPLETE (November 2025)

**🎯 Final Results:**
- **Enhanced Accuracy:** 83.91% (803/957 valid questions)
- **Baseline Accuracy:** 81.61% (781/957 valid questions)
- **Improvement:** +2.30% (+22 questions, 13.8% error reduction)
- **Best Databases:** pets_1, poker_player, wta_1 (100% accuracy)
- **Documentation Generated:** 120 semantic layer documents (6 types × 20 databases)
- **Total Cost:** ~$157 (within $110-195 budget)
- **Generation Time:** 2-4 hours automated vs weeks manual

**Key Achievements:**
- ✅ Fully automated semantic layer generation for 20 databases
- ✅ Comprehensive benchmark evaluation system with 1,034 questions
- ✅ Deterministic, reproducible results (temperature=0.0)
- ✅ Dual database support: Turso (SQLite) + Supabase (PostgreSQL)
- ✅ Production deployment on Vercel (frontend) and Railway (backend)
- ✅ Complete documentation and analysis
- ✅ Open-source release with MIT license

**📄 See [RESULTS.md](RESULTS.md) for complete analysis and findings.**

## What is QueryDawg?

QueryDawg addresses a critical gap in text-to-SQL systems: the semantic disconnect between how databases are structured (technical schemas) and how business users think about data (business language).

**The Solution:** Automatically generated natural language documentation that describes databases in business terms—including column purposes, synonyms, relationships, and common query patterns. This "semantic layer" enables more accurate SQL generation while simultaneously serving as valuable documentation.

## Key Features

- **🗄️ Dual Database Support**: Choose between Turso (native SQLite) or Supabase (PostgreSQL) per benchmark run
- **🎯 Database-Specific Prompts**: LLM prompts automatically adapt to SQL dialect (SQLite vs PostgreSQL)
- **🤖 Auto-Generated Semantic Layers**: LLM-generated business-context documentation for databases
- **📊 Spider 1.0 Benchmark System**: Full evaluation suite with 1,034 questions across 20 databases
- **🔍 Advanced SQL Comparison**: Execute and compare gold/baseline/enhanced SQL side-by-side
- **🎯 Intelligent Filtering**: Filter results by baseline/enhanced pass/fail for detailed analysis
- **⚡ Real-Time Metrics**: Live tracking of execution match rates during benchmark runs
- **🔄 SQLite → PostgreSQL Conversion**: Automatic query translation with GROUP BY expansion and mixed aggregate handling
- **🎨 Column-Order-Independent Matching**: Results comparison ignores column order differences
- **☁️ Production-Ready**: Cloud-deployable on Vercel (frontend) and Railway (backend)

## System Features (Project Complete)

**Backend (FastAPI):**
- Modular LLM architecture supporting multiple providers (OpenAI, Anthropic, Ollama)
- Database schema extraction from Supabase PostgreSQL
- Text-to-SQL generation with GPT-4o-mini (baseline & enhanced)
- **✨ Semantic Layer System:**
  - Automated LLM-powered documentation creation
  - Business context extraction (domain, entities, relationships)
  - Column-level semantic descriptions with synonyms
  - Query pattern identification and ambiguity detection
  - Vector embeddings with Pinecone for RAG-based semantic retrieval
  - Supabase metadata storage with version control
- **✨ Spider 1.0 Benchmark System:**
  - Full evaluation suite (1,034 questions, 20 databases)
  - Baseline vs Enhanced comparison runs
  - Execution match & exact match scoring
  - Real-time progress tracking with live metrics
  - Budget controls and cost monitoring
  - Supabase storage for benchmark results
  - SQLite to PostgreSQL automatic conversion:
    - Double quote → single quote transformation
    - GROUP BY clause expansion for PostgreSQL strictness
    - Mixed aggregate function handling
  - Column-order-independent result matching using frozensets
- SQL query execution with safety limits (max rows, timeout)
- Cost and performance tracking per query
- Background task processing for long-running benchmarks

**Frontend (Next.js 14):**
- Modern UI with shadcn/ui components and Tailwind CSS
- Database selector with 20 Spider datasets
- Natural language query interface with real-time SQL generation
- Interactive result display with execution metrics
- Cost and token usage tracking
- **✨ Semantic Layer Admin Interface:**
  - Generate semantic layers for databases
  - View and manage existing semantic layers
  - Preview LLM prompts before generation
  - Custom instructions for domain-specific context
  - Delete and regenerate semantic layers
  - Visual metadata display with embedding status
- **✨ Benchmark Control Panel:**
  - Configure and launch benchmark runs (baseline/enhanced/both)
  - Database selection and question limit controls
  - Real-time progress monitoring with auto-refresh
  - View detailed results with filtering:
    - Filter by baseline/enhanced pass/fail
    - Show failures only option
  - SQL comparison viewer with side-by-side display
  - Execute and compare all three SQLs (gold/baseline/enhanced)
  - View actual query results in tabular format
  - Run management (cancel, delete, view history)

**Infrastructure:**
- **Dual Database Sources:**
  - Turso (SQLite): 20 Spider databases in native SQLite format (zero conversion errors)
  - Supabase (PostgreSQL): 20 Spider databases with automatic SQLite→PostgreSQL conversion
- Semantic layers and benchmark results in Supabase
- Pinecone vector database for semantic embeddings
- RESTful API with OpenAPI documentation (/docs)
- Environment-based configuration
- Production deployment on Vercel (frontend) + Railway (backend)
- Background task processing for benchmark runs
- **Database-Specific LLM Prompts:** Automatic SQL dialect adaptation (SQLite vs PostgreSQL)

## Actual Results

- **83.91% enhanced accuracy** on Spider 1.0 (803/957 valid queries)
- **+2.30% improvement** over 81.61% baseline (+22 questions)
- **13.8% error reduction** (from 176 to 154 incorrect queries)
- **Automated documentation generation** (2-4 hours vs estimated weeks manual)
- **$0.01-0.02 cost per query** (within target)
- **19 diverse database domains** (excluding questions with gold SQL errors)
- **100% accuracy** on three databases (pets_1, poker_player, wta_1)
- **Broad improvements:** 11 databases improved, only 2 regressed

**Note:** Semantic layers provide dual value: modest but meaningful accuracy improvements (+2.30%) AND dramatic time savings (2-4 hours vs weeks). The 13.8% error reduction from an already-strong baseline demonstrates measurable impact.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 14, TypeScript, shadcn/ui, Tailwind CSS, Vercel |
| Backend | FastAPI, Python 3.11+, Railway |
| Database ORM | Drizzle ORM (TypeScript/Next.js), SQLAlchemy (Python/FastAPI) |
| Vector DB | Pinecone (semantic search) |
| SQL Database | Supabase PostgreSQL |
| LLM | OpenAI GPT-4o / GPT-4o-mini |
| UI Components | shadcn/ui (Radix UI + Tailwind CSS) |

## Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+, OpenAI API key, accounts for Vercel, Railway, Supabase, Pinecone

```bash
# Clone repository
git clone https://github.com/jsperson/querydawg.git
cd querydawg

# Backend setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Download Spider dataset (104MB, ~2-3 minutes)
python scripts/download_spider.py

# Test connections
python scripts/test_connections.py

# Frontend setup
cd frontend
npm install
npx shadcn-ui@latest init  # Initialize shadcn/ui with Tailwind CSS
cp .env.example .env.local
# Edit .env.local with your API endpoints

# Run locally
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

For detailed setup instructions, database loading, and semantic layer generation, see [docs/SETUP.md](docs/SETUP.md).

## Project Structure

```
querydawg/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI application entry
│   │   ├── config.py          # Configuration management
│   │   ├── llm/               # Modular LLM architecture
│   │   │   ├── base.py        # Base LLM interface
│   │   │   ├── openai_llm.py  # OpenAI implementation
│   │   │   ├── anthropic_llm.py  # Anthropic implementation
│   │   │   └── ollama_llm.py  # Ollama implementation
│   │   ├── database/          # Database operations
│   │   │   ├── schema_extractor.py       # Schema extraction
│   │   │   ├── supabase_schema_extractor.py  # Supabase-specific extraction
│   │   │   ├── sql_executor.py           # SQL execution
│   │   │   └── metadata_store.py         # Semantic layer storage
│   │   ├── services/          # Business logic
│   │   │   └── semantic_layer_generator.py  # LLM-powered semantic layer creation
│   │   └── routers/           # API endpoints
│   │       ├── databases.py   # Database listing
│   │       ├── schema.py      # Schema retrieval
│   │       ├── text_to_sql.py # SQL generation
│   │       ├── execute.py     # Query execution
│   │       └── semantic.py    # Semantic layer management
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Next.js 14 frontend
│   ├── src/
│   │   ├── app/              # App router
│   │   │   ├── page.tsx      # Main query interface
│   │   │   ├── layout.tsx    # Root layout
│   │   │   ├── admin/        # Admin interfaces
│   │   │   │   └── semantic/ # Semantic layer management
│   │   │   │       ├── page.tsx  # Admin interface
│   │   │   │       └── view/     # View semantic layers
│   │   │   │           └── page.tsx
│   │   │   └── api/          # API route handlers (proxy to backend)
│   │   │       ├── semantic/ # Semantic layer APIs
│   │   │       ├── databases/
│   │   │       ├── schema/
│   │   │       ├── text-to-sql/
│   │   │       └── execute/
│   │   ├── components/ui/    # shadcn/ui components
│   │   └── lib/
│   │       ├── api.ts        # API client
│   │       └── api-types.ts  # TypeScript types
│   └── package.json          # Node dependencies
├── data/
│   └── spider/               # Spider 1.0 dataset (200 databases)
│       ├── database/         # SQLite database files
│       ├── train_spider.json # Training questions
│       ├── train_others.json # Additional training data
│       └── dev.json          # Development/test questions
├── docs/
│   ├── project_plan.md       # Complete 7-week project plan
│   ├── progress_tracker.md   # Weekly progress tracking
│   └── SETUP.md             # Detailed setup guide (planned)
├── evaluation/               # Evaluation scripts (planned)
├── scripts/                  # Utility scripts
│   ├── download_spider.py    # Download Spider dataset
│   ├── verify_spider.py      # Verify dataset installation
│   ├── load_spider_databases.py  # Load databases to Supabase
│   └── test_connections.py   # Test all service connections
└── DEPLOYMENT.md             # Deployment guide
```

**Note:** The Spider dataset (~140MB) is not included in the repository. Run `python scripts/download_spider.py` to download it, or see [data/spider/DOWNLOAD.md](data/spider/DOWNLOAD.md) for manual instructions.

## Documentation

- **[Final Results](RESULTS.md)** - ⭐ **Complete analysis of final results, findings, and lessons learned**
- **[Project Plan](docs/project_plan.md)** - Original 7-week development plan, architecture, methodology, and research goals
- **[Progress Tracker](docs/progress_tracker.md)** - Detailed weekly progress tracking and milestone completion
- **[Deployment Guide](DEPLOYMENT.md)** - Step-by-step guide for deploying to Railway (backend) and Vercel (frontend)
- **[Spider Dataset Download](data/spider/DOWNLOAD.md)** - Instructions for downloading and setting up the Spider 1.0 dataset

### Analysis Documentation

- **[Run 22 Analysis](docs/prompt_optimization/RUN22_RESULTS_ANALYSIS.md)** - Final run analysis (best performance: 83.82%)
- **[Phase 2 Analysis](docs/phase2/RUN21_RESULTS_AND_PHASE2_CONCLUSION.md)** - Semantic layer optimization analysis
- **[Temperature Optimization](docs/temperature_optimization/TEST_RESULTS_ANALYSIS.md)** - Determinism validation tests
- **[Session State](docs/SESSION_STATE_2025-11-15.md)** - Final project state snapshot

## Research Context

This is an independent study project for the Master of Science in Data Science program at Newman University. The research question:

> "Can automatically generated natural language semantic layers bridge the semantic gap between database schemas and business language, resulting in significantly improved text-to-SQL accuracy while reducing documentation burden?"

**For complete research methodology, hypotheses, evaluation metrics, and timeline, see [docs/project_plan.md](docs/project_plan.md).**

## License

MIT License - See [LICENSE](LICENSE) file for details.

### Citation

If you use this work in your research or project, please cite:

```bibtex
@mastersproject{person2025querydawg,
  title={QueryDawg: Natural Language Semantic Layer for Text-to-SQL},
  author={Person, Jason Scott},
  year={2025},
  school={Newman University},
  type={Independent Study Project},
  url={https://github.com/jsperson/querydawg}
}
```

**Plain text citation:**
Person, J. S. (2025). *QueryDawg: Natural Language Semantic Layer for Text-to-SQL*. Independent Study Project, Newman University.

## Author

**Jason "Scott" Person** (jsperson@gmail.com)
Newman University
Master of Science in Data Science
Independent Study Project (2025)

## References

### Key Papers (Academic)
- Yu et al. (2018). [Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task](https://arxiv.org/abs/1809.08887) - Foundational benchmark dataset
- Lei et al. (2024). [Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows](https://arxiv.org/abs/2411.07763) - Enterprise complexity benchmark
- Automatic database description generation for Text-to-SQL (Feb 2025). [arXiv:2502.20657](https://arxiv.org/abs/2502.20657) - Recent work on auto-generating limited database descriptions

### Commercial & Open-Source Systems
- **AtScale** (2024). [Semantic Layer for Text-to-SQL](https://www.atscale.com/blog/enable-natural-language-prompting-with-semantic-layer-genai/) - 20% → 92.5% accuracy with manual semantic layer
- **App Orchid** (2025). [Ontology-Driven Text-to-SQL](https://www.apporchid.com/blog/%20how-app-orchids-ontology-driven-text-to-sql-solution-redefines-accuracy-and-trust-in-an-era-of-llm-hallucinations) - 99.8% accuracy on Spider 1.0 with manual ontologies
- **Wren AI** (2025). [Open-Source GenBI Agent](https://github.com/Canner/WrenAI) - Semantic layer requires dbt models or manual configuration
- **Vanna AI** (2024). [RAG-Powered Text-to-SQL](https://github.com/vanna-ai/vanna) - Open-source RAG framework requiring manual training data

### Datasets & Resources
- [Spider 1.0 Dataset](https://github.com/CrafterKolyan/spider-fixed) - 10,181 questions, 200 databases
- [Spider GitHub](https://github.com/taoyds/spider) - Official repository
- [OpenAI API Docs](https://platform.openai.com/docs) - LLM and embedding APIs
