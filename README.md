# DataPrism: Natural Language Semantic Layer for Text-to-SQL

A cloud-native text-to-SQL system that uses automatically generated natural language semantic layers to improve SQL query generation accuracy.

## What is DataPrism?

DataPrism addresses a critical gap in text-to-SQL systems: the semantic disconnect between how databases are structured (technical schemas) and how business users think about data (business language).

**The Solution:** Automatically generated natural language documentation that describes databases in business terms—including column purposes, synonyms, relationships, and common query patterns. This "semantic layer" enables more accurate SQL generation while simultaneously serving as valuable documentation.

## Key Features

- **Auto-Generated Semantic Layers**: LLM-generated business-context documentation for databases
- **Side-by-Side Comparison**: Compare baseline (schema-only) vs enhanced (with semantic layer) performance in real-time
- **Spider Benchmark Evaluation**: Rigorous testing on the industry-standard Spider 1.0 dataset
- **Production-Ready**: Cloud-deployed on Vercel (frontend) and Railway (backend)

## Expected Results

- **15-25% accuracy improvement** over schema-only approaches
- **Significant time reduction** in documentation creation (estimated hours vs weeks)
- **<$0.02 cost per query** in production use
- Support for 15-20 diverse database domains

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 14, TypeScript, Vercel |
| Backend | FastAPI, Python 3.11+, Railway |
| Vector DB | Pinecone (semantic search) |
| SQL Database | Supabase PostgreSQL |
| LLM | OpenAI GPT-4o / GPT-4o-mini |

## Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+, OpenAI API key, accounts for Vercel, Railway, Supabase, Pinecone

```bash
# Clone repository
git clone https://github.com/jsperson/dataprism.git
cd dataprism

# Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Frontend setup
cd ../frontend
npm install
cp .env.example .env.local
# Edit .env.local with your API endpoints

# Run locally
# Terminal 1: Backend
uvicorn app.main:app --reload

# Terminal 2: Frontend
npm run dev
```

For detailed setup instructions, database loading, and semantic layer generation, see [docs/SETUP.md](docs/SETUP.md).

## Project Structure

```
dataprism/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── data/            # Spider dataset
├── docs/            # Documentation
│   └── project_plan.md  # Complete project plan
├── evaluation/      # Evaluation scripts and results
└── scripts/         # Utility scripts
```

## Documentation

- **[Project Plan](docs/project_plan.md)** - Comprehensive 7-week development plan, architecture details, methodology, evaluation framework, and research goals
- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration (to be created)
- **[API Documentation](docs/API.md)** - Complete API reference (to be created)

## Research Context

This is an independent study project for the Master of Science in Data Science program at Newman University. The research question:

> "Can automatically generated natural language semantic layers bridge the semantic gap between database schemas and business language, resulting in significantly improved text-to-SQL accuracy while reducing documentation burden?"

**For complete research methodology, hypotheses, evaluation metrics, and timeline, see [docs/project_plan.md](docs/project_plan.md).**

## License

MIT License - See [LICENSE](LICENSE) file for details.

### Citation

If you use this work in your research or project, please cite:

```bibtex
@mastersproject{person2025dataprism,
  title={DataPrism: Natural Language Semantic Layer for Text-to-SQL},
  author={Person, Jason Scott},
  year={2025},
  school={Newman University},
  type={Independent Study Project},
  url={https://github.com/jsperson/dataprism}
}
```

**Plain text citation:**
Person, J. S. (2025). *DataPrism: Natural Language Semantic Layer for Text-to-SQL*. Independent Study Project, Newman University.

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
