# DataPrism: Natural Language Semantic Layer for Text-to-SQL
## 7-Week Independent Study Project Plan

---

## Project Metadata

**Student:** Jason "Scott" Person (jsperson@gmail.com)
**Institution:** Newman University, Wichita, KS
**Program:** Master of Science in Data Science
**Course:** Data Analytics Seminar (2025FA-BSAD-6873)
**Instructor:** Dr. David Cochran
**Timeline:** 7 weeks (2025-10-16 to 2025-12-04)

---

## Project Goal

**Demonstrate that natural language semantic layers can bridge the gap between database schemas and business understanding, enabling more accurate text-to-SQL generation while producing valuable documentation.**

## The Problem

Current text-to-SQL systems struggle with real-world queries because they lack business context, domain terminology, and implicit relationships. Research shows dramatic performance drops from academic benchmarks (top systems achieving 91% on Spider 1.0) to real-world enterprise tasks (some models achieving only ~20% on Spider 2.0).

## The Solution

Auto-generate natural language documentation that describes databases in business terms—column purposes, relationships, synonyms, query patterns. This semantic layer serves dual purposes:
1. Improves SQL generation accuracy
2. Provides valuable standalone documentation

## Novel Contributions

This project fills a specific gap in the current text-to-SQL landscape:

### What Already Exists
- **Commercial semantic layers** (AtScale, App Orchid, Wren AI) demonstrate dramatic accuracy improvements (20% → 92.5% for AtScale; 94.8% → 99.8% for App Orchid) but require **manual ontology creation** per database
- **Recent academic work** (Feb 2025) on automatic database description generation produces only **limited-scope descriptions** (under 20 words per column, under 100 words per table)
- **Open-source tools** (Vanna AI) use RAG for text-to-SQL but require **manual training data** (example queries, documentation)

### What's Novel in DataPrism
1. **Comprehensive Automatic Generation**: Among the first open-source systems to auto-generate complete semantic documentation including:
   - Database overviews with business context
   - Detailed table and column descriptions
   - Relationship explanations and join patterns
   - Query pattern libraries with examples
   - Business glossaries with domain terminology

   *(vs. existing work that generates only short column/table descriptions)*

2. **Dual-Purpose Value Proposition**: Explicitly evaluates documentation as both a means (better SQL) and an end (reusable asset), with hypothesis of significant time reduction compared to manual documentation

3. **Fully Automatic vs Manual**: Unlike App Orchid (99.8% accuracy with manual ontologies) or Wren AI (requires dbt models or manual configuration), DataPrism generates everything from schema alone

4. **Open-Source Research**: Reproducible evaluation on Spider 1.0 with cost/accuracy tradeoffs (mini vs full models), filling the gap between proprietary commercial tools and academic papers without implementations

5. **Systematic Comparative Evaluation**: Rigorous before/after testing on standard benchmark with 3-way comparison (baseline, enhanced-mini, enhanced-4o)

### Research Positioning

This work extends recent academic research (automatic description generation) from narrow scope to comprehensive documentation, while providing an open-source alternative to commercial semantic layer products. The 15-25% target accuracy improvement is achievable and meaningful, positioned between schema-only baselines (40-50%) and manual enterprise ontologies (92-99% as demonstrated by AtScale and App Orchid).

---

## Research Question

**"Can automatically generated natural language semantic layers bridge the semantic gap between database schemas and business language, resulting in significantly improved text-to-SQL accuracy while reducing documentation burden?"**

### Hypothesis

Natural language semantic layers will enable **15-25% higher execution accuracy** on text-to-SQL tasks compared to schema-only approaches, while requiring **significantly less time** to create than manual documentation (estimated hours vs. weeks).

---

## Key Deliverables

1. **Working Application** - Cloud-deployed system with side-by-side comparison
2. **Semantic Layers** - Auto-generated documentation for 15-20 Spider databases
3. **Evaluation Results** - Rigorous testing on 200+ Spider benchmark questions
4. **Technical Report** - 8-12 page summary of findings (foundation for future paper)
5. **Open Source Release** - Complete codebase with MIT license
6. **Demo Presentation** - Recorded demo and presentation materials

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VERCEL (Frontend)                    │
│               Next.js 14 + TypeScript                   │
│  - Query interface                                      │
│  - Comparison dashboard                                 │
│  - Evaluation results viewer                            │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS REST API
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  RAILWAY (Backend)                      │
│                  FastAPI (Python)                       │
│  - Schema extraction                                    │
│  - Semantic layer generation                            │
│  - Context retrieval (Pinecone)                         │
│  - Text-to-SQL generation                               │
│  - SQL execution                                        │
└───┬──────────────┬──────────────┬──────────────┬────────┘
    │              │              │              │
    ↓              ↓              ↓              ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ OpenAI   │  │Pinecone  │  │Supabase  │  │Supabase  │
│   API    │  │ Vectors  │  │PostgreSQL│  │ Tables   │
│GPT-4o    │  │Semantic  │  │Spider    │  │Semantic  │
│4o-mini   │  │Search    │  │Databases │  │Docs      │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| **Frontend** | Next.js 14, Vercel | Free |
| **Backend** | FastAPI, Railway | $10-15 |
| **Vector DB** | Pinecone | Free |
| **SQL Database** | Supabase PostgreSQL | Free |
| **LLM** | OpenAI API | $100-200 |
| **Total** | | **~$110-215** |

---

## Semantic Layer Design

### Document Types (per database)

For each database (e.g., `concert_singer`), the system generates:

1. **Database Overview** - Purpose, business context, key entities, typical use cases
2. **Table Descriptions** - Each table with business meaning, column details, common queries
3. **Relationships** - Foreign keys explained narratively, common join patterns
4. **Query Patterns** - Common question types, example queries with explanations
5. **Business Glossary** - Business terms, synonyms, domain terminology

### Storage

Stored as markdown-like text in Supabase, embedded in Pinecone for semantic retrieval:

```sql
CREATE TABLE semantic_layer.documents (
  id UUID PRIMARY KEY,
  database_name TEXT NOT NULL,
  document_type TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Spider Dataset Selection

**Source:** Yale Spider 1.0 - 10,181 questions, 5,693 SQL queries, 200 databases

**Selected 15-20 Databases** for diversity and complexity:

| Database | Domain | Tables | Complexity | Rationale |
|----------|--------|--------|------------|-----------|
| **concert_singer** | Entertainment | 3 | Medium | Clear relationships, common use case |
| **pets_1** | Pet care | 6 | Medium | Multiple entity types, many-to-many |
| **flight_2** | Aviation | 5 | Medium-High | Temporal queries, complex joins |
| **car_1** | Automotive | 8 | Medium-High | Many tables, nested relationships |
| **world_1** | Geography | 3 | Low-Medium | Large tables, good for aggregation |
| **student_transcripts_tracking** | Education | 6 | Medium-High | Academic domain, complex queries |
| **employee_hire_evaluation** | HR | 6 | Medium | Business domain, evaluation logic |
| **cre_Doc_Template_Mgt** | Document mgmt | 6 | High | Business terminology, complex schema |
| **course_teach** | Education | 3 | Low-Medium | Simple schema, good baseline |
| **museum_visit** | Culture | 3 | Medium | Date/time queries, visitor tracking |
| **wta_1** | Sports | 4 | Medium | Rankings, tournaments, stats |
| **battle_death** | Historical | 2 | Low | Simple schema, good for testing |
| **tvshow** | Entertainment | 4 | Medium | Temporal data, ratings |
| **poker_player** | Gaming | 3 | Medium | Statistics, rankings |
| **voter_1** | Politics | 3 | Medium | Demographic queries |
| **network_1** | Technology | 2 | Low-Medium | Network topology |
| **dog_kennels** | Pet services | 11 | High | Many tables, complex relationships |
| **singer** | Music | 2 | Low | Simple, good baseline |
| **real_estate_properties** | Real estate | 7 | Medium-High | Business domain, spatial data |
| **orchestra** | Music | 3 | Medium | Hierarchical data |

**Note:** Database selection is custom-curated based on domain diversity, complexity range (3-11 tables), and representative SQL patterns. Not an official Spider subset.

### Scope and Limitations

**What This Project Evaluates:**
- Spider 1.0 databases (foundational benchmark, well-established)
- Automatic generation from schema alone (no manual curation)
- Open-source, reproducible methodology

**Known Limitations:**
- Spider 1.0 databases are simpler than real enterprise systems (Spider 2.0 shows significant performance drops for most models)
- Auto-generated quality likely won't match manually-crafted ontologies (App Orchid's 99.8% with manual work)
- Limited to relational databases (SQLite/PostgreSQL)

**Why Spider 1.0 is Still Valuable:**
- Standard benchmark for reproducibility and comparison
- Foundation for future enterprise-scale work
- Sufficient complexity to demonstrate concept validity (200 databases, 10,181 questions)
- If successful, Spider 2.0 pilot (20-30 questions) demonstrates scalability potential

---

## 7-Week Timeline

### Week 1: Foundation & Baseline
**Goal:** Working baseline system deployed

**Key Tasks:**
- Set up infrastructure (Railway, Vercel, Supabase, Pinecone, OpenAI)
- Load 15-20 Spider databases into Supabase
- Build baseline text-to-SQL (schema only)
- Deploy to cloud
- Run baseline evaluation (50 questions)

**Deliverables:** Deployed baseline system, baseline accuracy measured

---

### Week 2: Semantic Layer Generation
**Goal:** Complete documentation for all databases

**Key Tasks:**
- Design generation prompts (overview, tables, relationships, patterns, glossary)
  - Build on recent research (arXiv:2502.20657) by extending from short descriptions to comprehensive documentation
  - Implement multi-stage generation: database → tables → columns → relationships → patterns
- Build generation pipeline using GPT-4o-mini/GPT-4o
- Process all 15-20 databases
- Quality review and refinement (manual spot-checking for hallucinations)
- Store in Supabase

**Deliverables:** Semantic layers for all databases (5 document types × 15-20 databases = 75-100 documents)

**Expected Cost:** ~$50-100 (GPT-4o for complex databases, GPT-4o-mini for simpler ones)

**Key Differentiator:** Unlike existing work that generates <20 word column descriptions, DataPrism generates comprehensive documentation including business context, query patterns, and glossaries

---

### Week 3: Vector Search & Retrieval
**Goal:** Semantic search working

**Key Tasks:**
- Set up Pinecone index
- Embed all semantic documents
- Build retrieval API (question → relevant context)
- Test and tune retrieval quality

**Deliverables:** Working semantic retrieval system

**Expected Cost:** ~$10-15

---

### Week 4: Enhanced Text-to-SQL
**Goal:** Integration complete

**Key Tasks:**
- Design enhanced prompts (schema + semantic context)
- Build enhanced text-to-SQL endpoint
- Add frontend comparison view
- End-to-end testing

**Deliverables:** Enhanced system with comparison capability

---

### Week 5: SQL Execution & Comparison
**Goal:** Safe execution and side-by-side comparison

**Key Tasks:**
- Build safe SQL execution engine
- Implement 3-way comparison (baseline, enhanced-mini, enhanced-4o)
- Polish UI
- Add metrics display

**Deliverables:** Production-ready comparison system

---

### Week 6: Comprehensive Evaluation
**Goal:** Rigorous benchmark results

**Key Tasks:**
- Build evaluation infrastructure
- Run 200-300 Spider questions through all 3 systems:
  - Baseline (schema only + GPT-4o-mini)
  - Enhanced (semantic layer + GPT-4o-mini)
  - Enhanced (semantic layer + GPT-4o)
- Calculate metrics (execution accuracy, cost, latency)
- Statistical analysis
- Create evaluation dashboard

**Deliverables:** Complete evaluation results with analysis

**Expected Cost:** ~$30-50

**Success Target:** 15-25% accuracy improvement with semantic layer

---

### Week 7: Documentation & Presentation
**Goal:** Polished deliverables

**Key Tasks:**
- Polish application UI
- Write technical summary report (8-12 pages)
- Create demo video (5-7 min)
- Build presentation slides
- Open source release (clean code, README, documentation)

**Deliverables:** Technical report, presentation, open-source repository

---

## Evaluation Metrics

### Primary Metric
**Execution Accuracy:** % of generated SQL queries that return correct results

### Targets

| System | Expected Accuracy |
|--------|-------------------|
| Baseline (schema only) | 40-50% (estimated) |
| Enhanced (with semantic layer) | 60-75% |
| **Target Improvement** | **15-25%** |

**Note:** Baseline estimates are based on typical schema-only performance in literature. Actual baseline will be measured during Week 1.

### Other Metrics
- Valid SQL rate (>90% target)
- Average latency (<5 seconds)
- Cost per query (<$0.02)
- Context relevance (manual evaluation)

---

## Budget

**Total Budget:** $110-195

### Breakdown

| Item | Cost | Notes |
|------|------|-------|
| OpenAI API (generation) | $50-100 | GPT-4o/GPT-4o-mini for semantic layers |
| OpenAI API (embeddings) | $10-15 | text-embedding-3-small |
| OpenAI API (development) | $10-15 | Testing |
| OpenAI API (evaluation) | $30-50 | 200-300 queries × 3 systems |
| Railway | $10-15 | Backend hosting |
| Other infrastructure | $0 | Free tiers |
| **Total** | **$110-195** | |

---

## Success Criteria

### Minimum Viable Success
- Working system deployed and operational
- Semantic layers generated for 15-20 databases
- Evaluation on 200+ questions
- **15-25% accuracy improvement** over baseline-estimated
- Cost analysis showing affordability
- Technical documentation complete

### Outstanding Success
- 25%+ accuracy improvement
- Ablation study showing which semantic components help most
- Spider 2.0 pilot evaluation (20-30 questions) demonstrating scalability to enterprise complexity
- Published open-source project with community interest
- Comparison against Vanna AI or other open-source baselines

---

## Risk Management

| Risk | Mitigation |
|------|------------|
| OpenAI costs exceed budget | Monitor daily, use mini model primarily, set API limits |
| Semantic layer quality poor | Iterate prompts early, manual review, regenerate if needed |
| Baseline accuracy too high | Use standard Spider metrics, adjust claims if needed |
| Behind schedule | Reduce database count (15→10), skip Spider 2.0 pilot |

---

## Extensions (If Time Permits)

- Ablation study (which semantic components matter most?)
- Human contributed semantic layer enhancements
- Spider 2.0 pilot on Snowflake (20-30 questions to demonstrate enterprise scalability)
- User study with classmates (documentation usefulness evaluation)
- Additional benchmarks (BIRD, WikiSQL)
- Comparative evaluation vs Vanna AI (open-source baseline)

---

## Expected Impact and Future Work

### Immediate Contributions
1. **Reproducible benchmark** for comprehensive semantic layer generation on Spider 1.0
2. **Open-source implementation** that practitioners can adapt for their databases
3. **Cost/accuracy tradeoffs** helping teams choose appropriate LLM configurations
4. **Dual-purpose framework** demonstrating documentation as both means and end

### Limitations Acknowledged
- Auto-generated quality likely won't match manually-crafted ontologies (App Orchid achieves 99.8% with manual work)
- Spider 1.0 databases simpler than real enterprise systems (Spider 2.0 features databases with 1000+ columns)
- Generated documentation may contain hallucinations requiring validation
- Limited to relational databases, not covering NoSQL or graph databases

### Future Research Directions
1. **Iterative refinement**: Human-in-the-loop improvements to auto-generated layers
2. **Enterprise scale**: Extending to Spider 2.0 databases (BigQuery, Snowflake) with 1000+ columns
3. **Domain specialization**: Fine-tuning generation for specific industries (healthcare, finance)
4. **Multi-modal generation**: Incorporating sample data, query logs, ER diagrams
5. **Hybrid approaches**: Combining automatic generation with manual expert knowledge
6. **Quality metrics**: Developing automated evaluation of semantic layer quality

### Broader Context

While commercial products demonstrate that semantic layers dramatically improve text-to-SQL accuracy (20% → 92.5%), they require expensive manual configuration. This project bridges the gap between "perfect but manual" and "automatic but limited," providing a practical middle ground suitable for:
- Medium-sized organizations lacking resources for manual ontology creation
- Rapid prototyping and initial database documentation
- Bootstrapping semantic layers later refined by domain experts
- Academic research requiring reproducible baselines

**Target Niche**: Organizations with 10-100 databases needing "good enough" automated documentation rather than "perfect" manual ontologies.

---

## References

### Key Papers (Academic)
- Yu et al. (2018). [Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task](https://arxiv.org/abs/1809.08887) - Foundational benchmark dataset
- Lei et al. (2024). [Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows](https://arxiv.org/abs/2411.07763) - Enterprise complexity benchmark
- Automatic database description generation for Text-to-SQL (Feb 2025). [arXiv:2502.20657](https://arxiv.org/abs/2502.20657) - Recent work on auto-generating limited database descriptions (0.93% improvement, 37% of human-level performance)

### Commercial & Open-Source Systems
- **AtScale** (2024). [Semantic Layer for Text-to-SQL](https://www.atscale.com/blog/enable-natural-language-prompting-with-semantic-layer-genai/) - 20% → 92.5% accuracy with manual semantic layer
- **App Orchid** (2025). [Ontology-Driven Text-to-SQL](https://www.apporchid.com/blog/%20how-app-orchids-ontology-driven-text-to-sql-solution-redefines-accuracy-and-trust-in-an-era-of-llm-hallucinations) - 99.8% accuracy on Spider 1.0 with manual ontologies per database
- **Wren AI** (2025). [Open-Source GenBI Agent](https://github.com/Canner/WrenAI) - Semantic layer requires dbt models or manual MDL configuration
- **Vanna AI** (2024). [RAG-Powered Text-to-SQL](https://github.com/vanna-ai/vanna) - Open-source RAG framework requiring manual training data

### Datasets & Resources
- [Spider 1.0 Dataset](https://github.com/CrafterKolyan/spider-fixed) - 10,181 questions, 200 databases
- [Spider GitHub](https://github.com/taoyds/spider) - Official repository
- [OpenAI API Docs](https://platform.openai.com/docs) - LLM and embedding APIs

---

## Repository Structure

```
dataprism/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/      # API endpoints
│   │   └── services/     # Core logic
│   └── requirements.txt
├── frontend/             # Next.js frontend
│   ├── app/
│   ├── components/
│   └── package.json
├── data/                 # Spider dataset
├── docs/
│   ├── project_plan.md   # This file
│   └── project_plan_long.md  # Detailed version
├── evaluation/           # Results and analysis
└── scripts/             # Utility scripts
```

---

## License

MIT License - Encourages adoption, contribution, and academic/commercial use.

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

---

## Development Notes

This project plan was developed collaboratively with Claude (Anthropic AI) as a research, analysis, and writing assistant. The collaboration included:
- Literature review and competitive landscape analysis (October 2025)
- Identification and summarization of relevant academic papers and commercial systems
- Positioning analysis of novel contributions relative to existing work
- Technical architecture suggestions and feasibility assessment
- Risk assessment and limitation identification
- Document drafting, structuring, and phrasing assistance

All strategic decisions, research direction, methodology choices, and final content remain the responsibility of the student. Claude served as a research and writing tool, not as a co-author or decision-maker.

---

*For the complete detailed version of this plan with comprehensive appendices, week-by-week task breakdowns, API specifications, and SQL schemas, see [project_plan_long.md](project_plan_long.md).*
