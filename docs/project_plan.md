# Natural Language Semantic Layer for Text-to-SQL
## Independent Study Project Plan

---

## Project Metadata

**Student:** Jason "Scott" Person 
**Institution:** Newman University, Wichita, KS  
**Program:** Master of Science in Data Science  
**Course:** Data Analytics Seminar (2025FA-BSAD-6873)  
**Instructor:** Dr. David Cochran  
**Project Type:** Independent Study  
**Timeline:** 7 weeks (flexible, with potential for extension)  
**Start Date:** 20251016 
**Expected Completion:** [Target Date]  

---

## Project Goal

**To demonstrate that natural language semantic layers can bridge the gap between database schemas and business understanding, enabling significantly more accurate text-to-SQL generation while simultaneously producing valuable documentation assets.**

## Executive Summary

This project addresses a critical challenge in enterprise data democratization: the semantic gap between how databases are structured and how business users think about data. Current text-to-SQL systems fail on 50-60% of real-world queries because they lack understanding of business context, domain terminology, and implicit relationships that aren't captured in database schemas.

**Core Innovation:** We propose a novel approach using **auto-generated natural language semantic layers** that serve as an interpretive bridge between raw database schemas and business language. Unlike existing solutions that rely on rigid ontologies or manual documentation, our system automatically generates rich, contextual documentation that describes databases in business terms - making the semantic layer both an enabler for better SQL generation AND a valuable documentation artifact in its own right.

**Measurable Objectives:**
1. Achieve **55-65% execution accuracy** on Spider benchmark (vs. 40-45% baseline)
2. Demonstrate **15-20% improvement** in query generation accuracy with semantic layer
3. Generate semantic documentation for **15-20 diverse databases** in under 2 hours
4. Reduce semantic layer creation time from weeks (manual) to hours (automated) - a **95% reduction**
5. Achieve **<$0.02 cost per query** in production use (including context retrieval)

**Key Deliverables:**
- Production-ready cloud application demonstrating real-time comparison
- Auto-generated semantic layers for 15-20 Spider databases
- Rigorous evaluation on 200+ Spider benchmark questions
- Open-source codebase and documentation (MIT License)
- Academic paper suitable for publication
- Live demo and presentation materials

---

## Research Question & Hypothesis

### Primary Research Question
**"Can automatically generated natural language semantic layers bridge the semantic gap between database schemas and business language, resulting in significantly improved text-to-SQL accuracy while reducing documentation burden?"**

### Secondary Research Questions
1. Which types of semantic information (column descriptions, relationships, synonyms, query patterns) contribute most to accuracy improvements?
2. Can the same semantic layer that improves SQL generation also serve as standalone technical documentation?
3. What is the optimal balance between semantic layer completeness and generation cost/time?

### Hypothesis
**Primary:** Natural language semantic layers that encode business context, domain terminology, and implicit relationships will enable LLMs to achieve **15-20% higher execution accuracy** on text-to-SQL tasks compared to using database schemas alone, while requiring **95% less time** to create than manual documentation (hours vs. weeks).

**Supporting Hypotheses:**
- H1: Business terminology and synonym mappings will have the highest impact on accuracy (expected: 5-8% improvement alone)
- H2: Relationship explanations will reduce JOIN errors by >30%
- H3: Query pattern examples will improve complex query accuracy by >20%
- H4: The semantic layer will be valuable as standalone documentation (measurable through readability and completeness metrics)

### Significance & Impact

**Academic Contribution:**
- First systematic study comparing natural language vs. structured semantic layers for text-to-SQL
- Novel evaluation framework measuring both accuracy AND documentation value
- Contribution to understanding which semantic information types matter most

**Practical Impact:**
- **Democratizes data access:** Non-technical users can query databases using natural language
- **Reduces documentation burden:** Auto-generates what typically takes weeks of manual effort
- **Dual-purpose solution:** Solves both the text-to-SQL problem AND the documentation problem
- **Enterprise-ready:** Cost-effective, maintainable, and scalable approach

**Why Current Solutions Fall Short:**
1. **Schema-only approaches:** Miss critical business context (40-50% accuracy ceiling)
2. **Structured ontologies:** Complex to create, hard to maintain, not human-readable
3. **Manual documentation:** Time-intensive, quickly becomes outdated, inconsistent quality
4. **Our solution:** Automated, maintainable, serves multiple purposes, leverages LLM strengths

---

## Architecture Overview

### System Components

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

### Technology Stack

| Component | Technology | Cost | Notes |
|-----------|-----------|------|-------|
| **Frontend** | Next.js 14, Vercel | Free | React, TypeScript, Tailwind CSS |
| **Backend** | FastAPI, Railway | $5/mo | Python 3.11+, async/await |
| **Vector DB** | Pinecone | Free | 100K vectors, 1 index |
| **SQL Database** | Supabase PostgreSQL | Free | 500MB storage |
| **LLM** | OpenAI API | ~$100 | GPT-4o-mini + GPT-4o + embeddings |
| **Version Control** | GitHub | Free | MIT License |
| **Total** | | **~$105** | For entire 7-week project |

---

## Semantic Layer Design

### Natural Language Format

Instead of structured schemas, we generate **natural language markdown documents**. These are text documents you will create during Week 2 of the project using GPT-4o-mini.

> **Important Note:** The file names mentioned below (like `relationships.md`, `glossary.md`, etc.) are **examples of document types you will generate** during Week 2. These are not existing files or clickable links - they represent the structure and naming convention for the semantic documentation your system will create. The actual content will be stored as text in Supabase and embedded in Pinecone for retrieval.

#### Document Types (per database)

For each database (e.g., `concert_singer`), your system will generate these document types:

**1. Database Overview**
   - What the database is about
   - Business context and purpose
   - Key entities
   - Typical use cases
   - Example filename: `database_overview.md`

**2. Table Descriptions** (one per table)
   - Table purpose in business terms
   - Each column with:
     - What it is (plain English)
     - Business meaning
     - Synonyms/alternate names
     - Example values
     - Usage patterns
   - Common queries involving this table
   - Example filenames: `table_singer.md`, `table_concert.md`, `table_stadium.md`

**3. Relationships Document**
   - Foreign key relationships explained narratively
   - Business meaning of relationships
   - Common join patterns
   - Example filename: `relationships.md`

**4. Query Patterns Document**
   - Common question types
   - Example queries with explanations
   - SQL patterns for this domain
   - Example filename: `query_patterns.md`

**5. Business Glossary**
   - Business terms and definitions
   - Synonyms and alternate phrasings
   - Domain-specific terminology
   - Example filename: `glossary.md`

#### Conceptual Organization

While stored as text in Supabase, the documents are conceptually organized like this:

```
semantic_layer_docs/ (stored in Supabase, organized by database_name + document_type)

concert_singer database:
  - database_overview
  - table_singer
  - table_concert  
  - table_stadium
  - relationships
  - query_patterns
  - glossary

pets_1 database:
  - database_overview
  - table_pets
  - table_owners
  - table_procedures
  - relationships
  - query_patterns
  - glossary
```

### Storage (Supabase)

Simple document storage table:

```sql
CREATE SCHEMA semantic_layer;

CREATE TABLE semantic_layer.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  database_name TEXT NOT NULL,
  document_type TEXT NOT NULL, -- 'overview', 'table', 'relationships', 'queries', 'glossary'
  title TEXT NOT NULL,
  content TEXT NOT NULL, -- Full markdown content
  metadata JSONB, -- Light metadata: {table_name, tags, etc}
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast retrieval
CREATE INDEX idx_documents_database ON semantic_layer.documents(database_name);
CREATE INDEX idx_documents_type ON semantic_layer.documents(document_type);

-- Full text search
CREATE INDEX idx_documents_content_fts ON semantic_layer.documents 
  USING gin(to_tsvector('english', content));
```

### Why Natural Language?

- ✅ Human-readable and maintainable
- ✅ Easy to version control (git-friendly)
- ✅ LLMs excel at processing natural language
- ✅ No rigid schema to constrain documentation
- ✅ Can be reviewed/edited by domain experts
- ✅ Valuable as standalone documentation

### Example Content

Here's what a generated table document might look like:

```markdown
# Singer Table

## Purpose
Stores information about individual singers including their personal details and career information.

## Business Description
Each row represents a unique singer. This is the central table for performer information and is frequently joined with the concert table to analyze singer activity and popularity.

## Columns

### singer_id
- **What it is**: Unique identifier for each singer
- **Data type**: Integer, primary key
- **Business meaning**: Used to link singers to their concerts
- **Also known as**: performer ID, artist ID
- **Example values**: 1, 2, 3

### name
- **What it is**: The singer's full name or stage name
- **Business meaning**: How the singer is publicly known
- **Also known as**: artist name, performer name, stage name
- **Example values**: "John Doe", "The Amazing Singer", "Jane Smith"
- **Common patterns**: May include both first and last names or just stage names

### birth_year
- **What it is**: The year the singer was born
- **Data type**: Integer (year)
- **Business meaning**: Used to calculate age and analyze career length
- **Also known as**: DOB year, year born
- **Example values**: 1990, 1985, 1978
- **Usage notes**: Some singers may have NULL values if birth year is unknown

### net_worth_millions
- **What it is**: Estimated net worth in millions of dollars
- **Business meaning**: Indicates the singer's financial success and market value
- **Also known as**: wealth, estimated value, financial worth
- **Example values**: 5.2, 150.0, 0.8
- **Usage notes**: Values are estimates and may not be precise

### citizenship
- **What it is**: The country of the singer's citizenship
- **Business meaning**: Used for geographic analysis and international tour planning
- **Also known as**: nationality, country of origin
- **Example values**: "United States", "United Kingdom", "Canada"

## Common Queries Involving This Table

1. "List all singers" → SELECT * FROM singer
2. "Who are the wealthiest singers?" → SELECT name, net_worth_millions FROM singer ORDER BY net_worth_millions DESC
3. "Find singers born after 1990" → SELECT name FROM singer WHERE birth_year > 1990
4. "Count singers by citizenship" → SELECT citizenship, COUNT(*) FROM singer GROUP BY citizenship
```
---

## Spider Dataset & Database Selection

### Spider 1.0 Overview
- **Source:** [Yale Spider Challenge](https://yale-lily.github.io/spider)
- **Size:** 10,181 questions, 5,693 unique SQL queries, 200 databases
- **Domains:** 138 different domains (music, flights, pets, education, etc.)
- **Format:** SQLite databases
- **Benchmark:** Industry-standard for text-to-SQL evaluation

### Recommended Database Subset (15-20 databases)

Selected for diversity and complexity:

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

**Selection Criteria:**
- Domain diversity (entertainment, education, business, etc.)
- Complexity range (2-11 tables)
- Mix of simple and complex relationships
- Representative of real-world use cases
- Good coverage of SQL patterns (joins, aggregations, temporal queries)

### Data Setup Resources

1. **Download Spider 1.0:**
   ```
   https://drive.google.com/uc?export=download&id=1iRDVHLr4mX2wQKSgA9J8Pire73Jahh0m
   ```

2. **GitHub Repository:**
   ```
   https://github.com/taoyds/spider
   ```

3. **Dataset Structure:**
   ```
   spider/
   ├── database/          # SQLite databases
   │   ├── concert_singer/
   │   ├── pets_1/
   │   └── ...
   ├── train_spider.json  # Training questions
   ├── train_others.json
   ├── dev.json          # Development/test questions
   └── tables.json       # Schema metadata
   ```

4. **SQLite to PostgreSQL Conversion:**
   - Use `pgloader` tool: https://github.com/dimitri/pgloader
   - Or Python script with `sqlite3` + `psycopg2`
   - Load into Supabase as separate schemas

---

## Detailed Week-by-Week Plan

### Week 1: Foundation & Baseline System
**Goal:** Working baseline text-to-SQL system deployed to cloud

#### Setup (Days 1-2)
- [ ] Create accounts:
  - Railway (backend hosting)
  - Vercel (frontend hosting)
  - Supabase (PostgreSQL database)
  - Pinecone (vector database)
  - OpenAI (API access)
- [ ] Set up GitHub repository
- [ ] Initialize project structure:
  ```
  semantic-sql/
  ├── backend/          # FastAPI
  ├── frontend/         # Next.js
  ├── data/            # Spider dataset
  ├── docs/            # Documentation
  ├── evaluation/      # Test results
  └── PROJECT_PLAN.md
  ```

#### Data Loading (Days 3-4)
- [ ] Download Spider 1.0 dataset
- [ ] Select 15-20 databases from recommendation list
- [ ] Convert SQLite → PostgreSQL schemas
- [ ] Load into Supabase (separate schema per database)
- [ ] Create database catalog table
- [ ] Verify data integrity

#### Baseline Implementation (Days 5-6)
- [ ] FastAPI backend:
  - Schema extraction endpoint
  - Basic text-to-SQL endpoint (schema only)
  - SQL validation
- [ ] Next.js frontend:
  - Database selection dropdown
  - Question input
  - SQL display
  - Results table
- [ ] Deploy to Railway + Vercel
- [ ] Test end-to-end flow

#### Baseline Evaluation (Day 7)
- [ ] Run baseline on 50 test questions
- [ ] Measure baseline accuracy
- [ ] Document baseline performance
- [ ] Identify common failure patterns

**Deliverables:**
- ✅ Deployed baseline system
- ✅ 15-20 databases loaded
- ✅ Baseline accuracy measured
- ✅ Infrastructure fully operational

---

### Week 2: Semantic Layer Generation
**Goal:** Rich natural language documentation for all databases

#### Database Setup (Day 1)
- [ ] Create Supabase schema for semantic documents
- [ ] Set up document storage tables
- [ ] Create indexes for fast retrieval

#### Prompt Engineering (Days 2-3)
- [ ] Design prompts for:
  - Database overviews
  - Table descriptions
  - Column metadata
  - Relationship explanations
  - Query patterns
  - Business glossaries
- [ ] Test prompts on 2-3 sample databases
- [ ] Iterate based on quality
- [ ] Create prompt template library

#### Generation Pipeline (Days 4-6)
- [ ] Build semantic layer generator:
  - Analyze database schema
  - Sample data extraction
  - Call GPT-4o-mini with prompts
  - Parse and store responses
  - Handle errors and retries
- [ ] Process all 15-20 databases
- [ ] Manual quality review of outputs
- [ ] Refine and regenerate if needed

#### Documentation (Day 7)
- [ ] Review generated semantic layers
- [ ] Create examples for presentation
- [ ] Document generation process
- [ ] Calculate generation costs

**Deliverables:**
- ✅ Complete semantic layer for all databases
- ✅ Documented generation methodology
- ✅ Quality-reviewed documentation
- ✅ Cost analysis for generation

**Expected Cost:** ~$25-35 for semantic layer generation

---

### Week 3: Vector Search & Context Retrieval
**Goal:** Semantic search system for finding relevant documentation

#### Pinecone Setup (Day 1)
- [ ] Initialize Pinecone index
- [ ] Configure dimensions (1536 for OpenAI embeddings)
- [ ] Set up metadata filtering

#### Embedding Strategy (Days 2-3)
- [ ] Design chunking strategy for documents
- [ ] Embed all semantic documents:
  - Database overviews
  - Table descriptions
  - Relationships
  - Query patterns
  - Glossary terms
- [ ] Upload to Pinecone with metadata
- [ ] Verify embeddings

#### Retrieval Implementation (Days 4-5)
- [ ] Build retrieval API:
  - Question embedding
  - Pinecone search
  - Result ranking
  - Context assembly
- [ ] Implement relevance scoring
- [ ] Test retrieval quality manually

#### Testing & Tuning (Days 6-7)
- [ ] Test retrieval on sample questions
- [ ] Evaluate precision/recall manually
- [ ] Tune top-k parameter
- [ ] Adjust chunking if needed
- [ ] Document retrieval strategy

**Deliverables:**
- ✅ Working semantic retrieval system
- ✅ All documents embedded and searchable
- ✅ Retrieval quality validated
- ✅ API documentation

**Expected Cost:** ~$10-15 for embeddings

---

### Week 4: Enhanced Text-to-SQL System
**Goal:** Complete text-to-SQL with semantic layer integration

#### Prompt Engineering (Days 1-2)
- [ ] Design enhanced prompts:
  - Question + Schema + Semantic Context
  - Structured formatting
  - Clear instructions
- [ ] Test with/without different context types
- [ ] Optimize prompt structure

#### Integration (Days 3-4)
- [ ] Build enhanced text-to-SQL endpoint:
  - Retrieve semantic context
  - Build enriched prompt
  - Call OpenAI API
  - Parse SQL response
  - Validate SQL
- [ ] Support both GPT-4o-mini and GPT-4o
- [ ] Add error handling

#### Frontend Updates (Days 5-6)
- [ ] Add context visualization:
  - Show retrieved documents
  - Highlight relevant portions
  - Display confidence scores
- [ ] System selection (baseline vs enhanced)
- [ ] Improve UI/UX

#### Testing (Day 7)
- [ ] End-to-end testing
- [ ] Compare baseline vs enhanced manually
- [ ] Fix bugs
- [ ] Performance optimization

**Deliverables:**
- ✅ Enhanced text-to-SQL system working
- ✅ Context visualization
- ✅ Comparison capability
- ✅ Stable, tested system

**Expected Cost:** ~$10-15 for development testing

---

### Week 5: SQL Execution & Comparison Mode
**Goal:** Safe SQL execution and side-by-side comparison

#### Execution Engine (Days 1-2)
- [ ] Build safe SQL execution:
  - Query validation (prevent DROP, DELETE, UPDATE)
  - Timeout handling
  - Error catching
  - Result formatting
- [ ] Test on all databases
- [ ] Handle edge cases

#### Comparison System (Days 3-4)
- [ ] Build comparison endpoint:
  - Run same question through both systems
  - Execute both SQL queries
  - Compare results
  - Calculate metrics
- [ ] Support 3-way comparison:
  - Baseline (schema only)
  - Enhanced + GPT-4o-mini
  - Enhanced + GPT-4o

#### Frontend Polish (Days 5-6)
- [ ] Build comparison UI:
  - Side-by-side SQL display
  - Results comparison
  - Context used display
  - Metrics (latency, cost)
- [ ] Add error messages
- [ ] Loading states
- [ ] Responsive design

#### Documentation (Day 7)
- [ ] User documentation
- [ ] API documentation
- [ ] Demo scenarios
- [ ] Screenshots

**Deliverables:**
- ✅ Safe SQL execution
- ✅ Comparison mode working
- ✅ Polished UI
- ✅ Ready for evaluation

**Expected Cost:** ~$5-10 for testing

---

### Week 6: Comprehensive Evaluation
**Goal:** Rigorous evaluation on Spider 1.0 benchmark

#### Evaluation Infrastructure (Days 1-2)
- [ ] Create evaluation database schema:
  - Runs table
  - Results table
  - Metrics tables
- [ ] Build evaluation runner:
  - Load Spider test questions
  - Run through both systems
  - Execute SQL
  - Compare results
  - Track metrics

#### Spider 1.0 Evaluation (Days 3-5)
- [ ] Run evaluation on dev set (200-300 questions)
- [ ] For each system:
  - Baseline
  - Enhanced + GPT-4o-mini
  - Enhanced + GPT-4o
- [ ] Calculate metrics:
  - Execution accuracy
  - Valid SQL rate
  - Average latency
  - Total cost
  - Error types
- [ ] Store all results

#### Analysis (Days 6-7)
- [ ] Statistical analysis:
  - Accuracy improvement
  - Significance testing
  - Error analysis
  - Cost-benefit analysis
- [ ] Create visualizations:
  - Accuracy by system
  - Accuracy by question complexity
  - Error type distribution
  - Cost per query
- [ ] Build evaluation dashboard

#### Spider 2.0 Pilot (Optional - if ahead of schedule)
- [ ] Set up Snowflake free trial
- [ ] Load 3-5 Spider 2.0-Snow databases
- [ ] Run 20-30 test questions
- [ ] Document challenges and results
- [ ] Position as future work

**Deliverables:**
- ✅ Complete evaluation results
- ✅ Statistical analysis
- ✅ Evaluation dashboard
- ✅ Documented findings
- ✅ (Optional) Spider 2.0 pilot results

**Expected Cost:** ~$30-50 for evaluation runs

**Success Metrics:**
- **Target:** 15-25% accuracy improvement with semantic layer
- **Baseline:** 40-50% execution accuracy (typical for schema-only)
- **Enhanced:** 60-75% execution accuracy (with semantic layer)

---

### Week 7: Polish, Documentation & Presentation
**Goal:** Production-ready demo and comprehensive documentation

#### Application Polish (Days 1-2)
- [ ] Landing page with project description
- [ ] About/documentation pages
- [ ] Clean, professional UI
- [ ] Mobile responsiveness
- [ ] Performance optimization
- [ ] Deploy to production URLs

#### Academic Paper (Days 3-5)
- [ ] Draft paper structure:
  1. Abstract
  2. Introduction & Motivation
  3. Related Work
  4. Methodology
  5. Implementation
  6. Evaluation & Results
  7. Analysis & Discussion
  8. Future Work
  9. Conclusion
- [ ] Write sections iteratively
- [ ] Create figures and tables
- [ ] References and citations

#### Presentation Materials (Days 6-7)
- [ ] Demo video (5-7 minutes):
  - System overview
  - Live demo
  - Results highlight
- [ ] Slide deck (15-20 slides):
  - Problem statement
  - Approach
  - Architecture
  - Demo
  - Results
  - Conclusions
- [ ] Practice presentation
- [ ] Prepare Q&A responses

#### Open Source Release
- [ ] Clean up code
- [ ] Comprehensive README
- [ ] Setup instructions
- [ ] API documentation
- [ ] License file (MIT)
- [ ] Contributing guidelines
- [ ] Make repository public

**Deliverables:**
- ✅ Production-ready application
- ✅ Academic paper draft
- ✅ Presentation materials
- ✅ Open-source repository
- ✅ Complete documentation

---

## Evaluation Metrics & Success Criteria

### Primary Metric
**Execution Accuracy:** Percentage of generated SQL queries that return the same results as gold standard queries when executed.

### Success Criteria

**Minimum Viable Success:**
- ✅ Working system deployed and operational
- ✅ Semantic layer generated for 15-20 databases
- ✅ Evaluation on 200+ Spider 1.0 questions
- ✅ **15-25% accuracy improvement** over baseline
- ✅ Cost analysis showing affordability
- ✅ Complete documentation

**Outstanding Success:**
- ⭐ 25%+ accuracy improvement
- ⭐ Ablation study (which metadata types help most)
- ⭐ Spider 2.0 pilot with meaningful results
- ⭐ Published open-source project with community interest
- ⭐ Publishable research findings
- ⭐ Production deployment handling real traffic

### Detailed Metrics to Track

| Metric | Description | Target |
|--------|-------------|--------|
| **Execution Accuracy** | % queries returning correct results | 60-75% (enhanced) vs 40-50% (baseline) |
| **Valid SQL Rate** | % queries that parse and execute | >90% |
| **Exact Match Accuracy** | % queries matching gold SQL exactly | 30-45% (reference only) |
| **Average Latency** | Time per query (generation + execution) | <5 seconds |
| **Cost per Query** | OpenAI API cost per query | <$0.01 |
| **Context Relevance** | % of retrieved docs rated as relevant | >80% (manual evaluation) |
| **Error Rate by Type** | Distribution of error types | Documented |

### Evaluation Framework

**Test Sets:**
- **Development Set:** 200-300 questions from Spider dev.json
- **Complexity Levels:** Easy, Medium, Hard, Extra Hard
- **Query Types:** Simple SELECT, JOINs, Aggregations, Nested queries, Set operations

**Comparison Groups:**
1. **Baseline:** Schema only + GPT-4o-mini
2. **Enhanced Mini:** Schema + Semantic Layer + GPT-4o-mini
3. **Enhanced 4o:** Schema + Semantic Layer + GPT-4o

**Statistical Analysis:**
- Accuracy improvement calculation
- Confidence intervals
- Paired t-tests for significance
- Error type categorization
- Cost-benefit analysis

---

## Budget & Cost Tracking

### Total Budget: $100-125

### Cost Breakdown

| Item | Estimated Cost | Notes |
|------|----------------|-------|
| **OpenAI API** | | |
| - Semantic generation | $25-35 | GPT-4o-mini for doc generation |
| - Embeddings | $10-15 | text-embedding-3-small |
| - Development testing | $10-15 | Testing both systems |
| - Evaluation runs | $30-50 | 200-300 queries × 3 systems |
| **Infrastructure** | | |
| - Railway | $5 | Covered by free credit |
| - Vercel | $0 | Free tier |
| - Supabase | $0 | Free tier |
| - Pinecone | $0 | Free tier |
| **Contingency** | $10-15 | Buffer for overages |
| **Total** | **$90-130** | Within budget |

### Cost Optimization Strategies
- Use GPT-4o-mini primarily (10x cheaper than GPT-4o)
- Use GPT-4o only for final evaluation comparison
- Batch API requests where possible
- Cache embeddings (don't regenerate)
- Monitor usage daily via OpenAI dashboard
- Set spending limits in OpenAI account

### Cost Tracking Template
```
Week | Semantic Gen | Embeddings | Testing | Evaluation | Total | Cumulative
-----|-------------|------------|---------|------------|-------|------------
1    | $0          | $0         | $5      | $0         | $5    | $5
2    | $30         | $0         | $5      | $0         | $35   | $40
3    | $0          | $12        | $3      | $0         | $15   | $55
4    | $0          | $0         | $8      | $0         | $8    | $63
5    | $0          | $0         | $10     | $0         | $10   | $73
6    | $0          | $0         | $5      | $40        | $45   | $118
7    | $0          | $0         | $5      | $0         | $5    | $123
```

---

## Deliverables

### 1. Working Application
- **URL:** [Production URL on Vercel]
- **Features:**
  - Question input interface
  - Database selection
  - Baseline vs Enhanced comparison
  - SQL visualization
  - Results display
  - Context viewer (what semantic docs were used)
  - Evaluation dashboard
- **Accessibility:** Public demo, responsive design

### 2. Semantic Layer Assets
- 15-20 databases with complete natural language documentation
- Organized markdown files
- Version controlled in repository
- Searchable via Pinecone

### 3. Evaluation Results
- **Comprehensive report including:**
  - Accuracy metrics (baseline vs enhanced)
  - Statistical significance testing
  - Error analysis
  - Cost analysis
  - Visualizations
- **Format:** Interactive dashboard + PDF report

### 4. Academic Paper
**Title:** "Natural Language Semantic Layers for Improved Text-to-SQL Generation"

**Structure:**
1. **Abstract** (200 words)
2. **Introduction** (2 pages)
   - Problem statement
   - Research question
   - Contributions
3. **Related Work** (2-3 pages)
   - Text-to-SQL systems
   - Semantic layers and ontologies
   - LLM-based approaches
4. **Methodology** (3-4 pages)
   - Natural language semantic layer design
   - Document types and generation
   - Retrieval strategy
   - Text-to-SQL pipeline
5. **Implementation** (2-3 pages)
   - Architecture
   - Technology choices
   - Key algorithms
6. **Evaluation** (3-4 pages)
   - Experimental setup
   - Metrics
   - Results
   - Statistical analysis
7. **Analysis & Discussion** (2-3 pages)
   - What works and why
   - Ablation studies
   - Error analysis
   - Limitations
8. **Future Work** (1 page)
   - Spider 2.0 extension
   - Production deployment
   - Multi-modal extensions
9. **Conclusion** (1 page)
10. **References**

**Target Length:** 15-20 pages
**Format:** ACM or IEEE conference format

### 5. Presentation
**Demo Presentation (15-20 minutes):**
- Problem and motivation (2 min)
- Approach overview (3 min)
- Architecture (2 min)
- Live demo (5 min)
  - Show baseline system
  - Show enhanced system
  - Compare side-by-side
- Results (3 min)
- Conclusions and future work (2 min)
- Q&A (10 min)

**Materials:**
- Slide deck (15-20 slides)
- Demo video (5-7 min) as backup
- Live demo environment
- Handout with key findings

### 6. Open Source Repository
**Repository:** [github.com/[your-username]/semantic-sql]
**License:** MIT

**Contents:**
- Complete source code (frontend + backend)
- Setup instructions
- API documentation
- Generated semantic layers (sample)
- Evaluation scripts
- Results data
- Academic paper (preprint)
- README with:
  - Project overview
  - Quick start guide
  - Architecture diagram
  - Results summary
  - Citation instructions

---

## Risk Management

### Identified Risks & Mitigation Strategies

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **OpenAI costs exceed budget** | Medium | High | Monitor daily, use mini model primarily, set API limits |
| **Semantic layer quality is poor** | Medium | High | Iterate prompts early (Week 2), manual review, regenerate if needed |
| **Retrieval not finding relevant docs** | Medium | Medium | Test early (Week 3), adjust chunking strategy, tune parameters |
| **Baseline accuracy too high** | Low | Medium | Use standard Spider baseline metrics, adjust claim if needed |
| **Evaluation takes too long** | Medium | Low | Start with subset (100 questions), scale up, parallelize |
| **Spider 2.0 too complex** | High | Low | Keep as optional stretch goal, don't block core work |
| **Infrastructure downtime** | Low | Medium | Use reliable providers (Vercel, Railway), have backups |
| **Data loading issues** | Low | Medium | Test SQLite→PostgreSQL conversion early, validate data |
| **Scope creep** | Medium | High | Stick to plan, track hours, defer nice-to-haves |
| **Time management** | Medium | Medium | Weekly check-ins, adjust if ahead/behind |

### Contingency Plans

**If behind schedule:**
1. Reduce database count (15 → 10)
2. Skip Spider 2.0 pilot
3. Simplify UI
4. Focus on core functionality

**If ahead of schedule:**
1. Add Spider 2.0 pilot
2. Implement ablation study
3. Add more databases
4. Enhanced visualizations
5. User testing with classmates

**If costs exceed budget:**
1. Switch to GPT-4o-mini exclusively
2. Reduce evaluation question count
3. Use cached results where possible
4. Stop evaluation early if trend clear

---

## Resources & References

### Key Papers

1. **Spider 1.0 Paper:**
   - Yu et al. (2018). "Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task"
   - https://arxiv.org/abs/1809.08887

2. **Spider 2.0 Paper:**
   - Lei et al. (2024). "Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows"
   - https://arxiv.org/abs/2411.07763

3. **BIRD Benchmark:**
   - Li et al. (2024). "BIRD: A Big Benchmark for Large-scale Database Grounded Text-to-SQL Evaluation"
   - https://arxiv.org/abs/2305.03111

4. **Semantic Layers:**
   - AtScale white paper: "Enabling Natural Language Prompting with Semantic Layer and Generative AI"
   - App Orchid blog: Ontology-driven Text-to-SQL

5. **LLM Text-to-SQL Survey:**
   - "A Survey on Employing Large Language Models for Text-to-SQL Tasks"
   - https://arxiv.org/abs/2407.15186

### Datasets & Tools

- **Spider 1.0:** https://yale-lily.github.io/spider
- **Spider 2.0:** https://spider2-sql.github.io/
- **GitHub (Spider):** https://github.com/taoyds/spider
- **GitHub (Spider2):** https://github.com/xlang-ai/Spider2

### Documentation

- **OpenAI API:** https://platform.openai.com/docs
- **Pinecone:** https://docs.pinecone.io
- **Supabase:** https://supabase.com/docs
- **Railway:** https://docs.railway.app
- **Vercel:** https://vercel.com/docs
- **FastAPI:** https://fastapi.tiangolo.com
- **Next.js:** https://nextjs.org/docs

### Community & Support

- **Spider Leaderboard:** Track SOTA results
- **Discord/Slack:** Text-to-SQL communities
- **GitHub Issues:** For specific tool questions
- **Stack Overflow:** Technical problems

---

## Timeline Flexibility & Extensions

### Accelerated Timeline (If Ahead)
Given you have 10+ hours per week available:

**Week 4.5:** Ablation Study
- Test impact of individual semantic layer components
- Which doc types help most?
- Minimum effective semantic layer

**Week 5.5:** Spider 2.0 Pilot
- Full implementation on Snowflake
- 50-100 questions instead of 20-30
- More comprehensive enterprise evaluation

**Week 6.5:** User Study
- Recruit classmates/colleagues
- Evaluate usability
- Gather qualitative feedback

**Week 7.5:** Production Optimization
- Caching layer
- Rate limiting
- Multi-user support
- Analytics integration

### Extended Timeline (If More Time)
**Weeks 8-10:** Potential extensions
- Fine-tune smaller models on semantic data
- Multi-database queries
- Natural language result explanation
- Visualization generation
- Additional benchmarks (BIRD, WikiSQL)

---

## Appendices

### A. Supabase Schema Reference

```sql
-- Database catalog
CREATE TABLE public.databases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  domain TEXT,
  description TEXT,
  table_count INTEGER,
  loaded_at TIMESTAMP DEFAULT NOW()
);

-- Semantic layer documents
CREATE SCHEMA semantic_layer;

CREATE TABLE semantic_layer.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  database_name TEXT NOT NULL,
  document_type TEXT NOT NULL, 
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documents_database ON semantic_layer.documents(database_name);
CREATE INDEX idx_documents_type ON semantic_layer.documents(document_type);
CREATE INDEX idx_documents_content_fts ON semantic_layer.documents 
  USING gin(to_tsvector('english', content));

-- Evaluation results
CREATE SCHEMA evaluation;

CREATE TABLE evaluation.runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_name TEXT NOT NULL,
  system_type TEXT NOT NULL,
  model TEXT,
  test_set TEXT,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  total_questions INTEGER,
  successful_generations INTEGER,
  successful_executions INTEGER,
  execution_accuracy FLOAT,
  exact_match_accuracy FLOAT,
  total_cost_usd FLOAT,
  avg_latency_ms FLOAT
);

CREATE TABLE evaluation.results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID REFERENCES evaluation.runs(id),
  question_id TEXT,
  database TEXT,
  question TEXT,
  gold_sql TEXT,
  generated_sql TEXT,
  execution_match BOOLEAN,
  exact_match BOOLEAN,
  error_message TEXT,
  latency_ms INTEGER,
  cost_usd FLOAT,
  context_retrieved JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### B. API Endpoint Reference

**Backend (Railway):**
```
POST   /api/schema/extract          - Extract database schema
POST   /api/semantic/generate       - Generate semantic layer
POST   /api/semantic/retrieve       - Retrieve relevant context
POST   /api/sql/baseline           - Generate SQL (baseline)
POST   /api/sql/enhanced           - Generate SQL (with semantic layer)
POST   /api/sql/execute            - Execute SQL query
POST   /api/sql/compare            - Compare systems
POST   /api/evaluate/run           - Run evaluation
GET    /api/evaluate/results/{id}  - Get evaluation results
GET    /api/databases              - List available databases
```

### C. Repository Structure

```
semantic-sql/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── schema.py
│   │   │   ├── semantic.py
│   │   │   ├── sql.py
│   │   │   └── evaluate.py
│   │   ├── services/
│   │   │   ├── openai_service.py
│   │   │   ├── pinecone_service.py
│   │   │   ├── supabase_service.py
│   │   │   └── generator.py
│   │   └── models/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── query/
│   │   ├── dashboard/
│   │   └── layout.tsx
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── next.config.js
├── data/
│   ├── spider/
│   └── scripts/
├── docs/
│   ├── API.md
│   ├── SETUP.md
│   └── EVALUATION.md
├── evaluation/
│   ├── results/
│   └── notebooks/
├── .env.example
├── .gitignore
├── LICENSE (MIT)
├── README.md
└── PROJECT_PLAN.md (this file)
```

### D. Weekly Check-in Questions

Use these for self-assessment each week:

1. Did I complete this week's deliverables?
2. Am I on track with the budget?
3. Are there any blockers?
4. Should I adjust the plan?
5. What went well this week?
6. What needs improvement?
7. Am I ahead or behind schedule?
8. Do I need help with anything?

### E. License Information

**MIT License - Why?**

The MIT License is ideal for this project because:
- ✅ Simple and permissive
- ✅ Allows commercial use
- ✅ Widely recognized and trusted
- ✅ Compatible with most other licenses
- ✅ Good for academic/research projects
- ✅ Encourages adoption and contribution

**I agree - MIT is the best choice for this project.**

Alternative considerations:
- Apache 2.0: If you want patent protection
- GPL: If you want to keep derivatives open
- For academic work, MIT is standard and appropriate

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [Date] | [Your Name] | Initial project plan |

---

## Approval & Sign-off

**Student Signature:** _________________________ Date: _____________

**Instructor Approval:** _________________________ Date: _____________

**Notes:**

---

*This document is a living plan and may be updated as the project progresses.*
