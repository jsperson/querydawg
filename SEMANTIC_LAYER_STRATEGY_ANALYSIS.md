# Semantic Layer Strategy Analysis

**Date**: 2025-11-03
**Purpose**: Compare current semantic layer approach with three proposed future strategies

---

## Executive Summary

| Strategy | Complexity | Accuracy Potential | Maintenance | Best For |
|----------|------------|-------------------|-------------|----------|
| **Current (RAG-based)** | Low | Medium (85-87%) | Low | General text-to-SQL, rapid iteration |
| **Multi-Agent Refinement** | High | High (90-95%) | Medium | Complex schemas, iterative improvement |
| **Ontology-Backed** | Very High | Very High (95%+) | High | Multi-domain, enterprise, compliance |
| **Metric-Centric Hub** | Medium-High | High (90-93%) | Medium-High | Analytics, BI, stable metrics |

**Recommendation**: Continue with current approach + Phase 1-2 improvements until we hit 85-87% accuracy. Consider **Metric-Centric Hub** as next major evolution for production deployment.

---

## Current Approach: RAG-Based Semantic Layer

### Architecture

```
Schema Extraction → LLM Generation → Semantic Layer (JSON)
                         ↓
                   Chunking + Embedding
                         ↓
                    Pinecone Vector Store
                         ↓
Question → Vector Search → Top-K Chunks → Enhanced Prompt → SQL
```

**Key Components**:
1. **Generation**: GPT-4o-mini generates business context from schema + sample data
2. **Storage**: JSON semantic layers with table docs, relationships, patterns
3. **Retrieval**: Vector search retrieves top-K relevant chunks (now 10)
4. **Enhancement**: Retrieved chunks added to prompt alongside live schema
5. **Generation**: LLM generates SQL with both technical + business context

### Characteristics

**Strengths**:
- ✅ Simple architecture (easy to understand and debug)
- ✅ Low implementation cost (~1 week to build)
- ✅ Fast iteration (regenerate semantic layers in minutes)
- ✅ Flexible (works with any database schema)
- ✅ No schema modification required
- ✅ Handles schema changes gracefully (live schema is ground truth)

**Weaknesses**:
- ❌ Retrieval quality varies (only 20-40% chunks highly relevant)
- ❌ No verification of semantic layer accuracy
- ❌ Generic chunks waste retrieval slots
- ❌ No learning from failures
- ❌ Limited to static documentation

**Current Performance**:
- Baseline: 83.2% accuracy
- Enhanced (before Phase 1): 80.9% accuracy (-2.3%)
- Enhanced (after Phase 1, expected): 84-86% accuracy (+1-3%)

**Cost**:
- Semantic layer generation: $0.06 for 20 databases
- Per query: $0.000675 (with 10 chunks)
- Embeddings: ~$0.0001 per database

---

## Strategy 1: Multi-Agent Schema Refinement

### Architecture

```
Schema → Planner Agent → Proposed SQL Views
              ↓
         Critic Agent → Feedback on Views
              ↓
       Verifier Agent → Execute & Validate Views
              ↓
      Store Verified Views as Semantic Layer
              ↓
Question → Match to Views (Embedding) → Generate SQL from Views
              ↓
         Failure? → Feed back to Planner
```

**Key Components**:
1. **Planner Agent**: Proposes SQL views that represent business concepts
2. **Critic Agent**: Reviews views for correctness, clarity, usefulness
3. **Verifier Agent**: Executes views against database to validate
4. **View Repository**: Stores verified views as executable semantic layer
5. **GraphRAG**: Clusters views and derives relationships
6. **Feedback Loop**: Failed queries improve future view proposals

### Example

**Raw Schema**:
```sql
TABLE matches (match_num, loser_id, winner_id, tourney_id)
TABLE players (player_id, first_name, country_code)
TABLE rankings (ranking_date, player_id, ranking)
```

**Proposed Views** (by Planner):
```sql
-- Planner proposes this view
CREATE VIEW player_match_summary AS
SELECT
  p.player_id,
  p.first_name,
  p.country_code,
  COUNT(DISTINCT m.match_num) as total_matches,
  COUNT(DISTINCT CASE WHEN m.winner_id = p.player_id THEN m.match_num END) as wins
FROM players p
LEFT JOIN matches m ON p.player_id IN (m.winner_id, m.loser_id)
GROUP BY p.player_id, p.first_name, p.country_code;
```

**Critic Feedback**:
- ✅ Correct: Captures player win statistics
- ⚠️ Suggestion: Add tournament filter capability
- ✅ Verified: View executes successfully

**Usage**:
- Question: "Which players won the most matches?"
- Retrieved View: `player_match_summary`
- Generated SQL: `SELECT first_name, wins FROM player_match_summary ORDER BY wins DESC LIMIT 10;`

### Characteristics

**Strengths**:
- ✅ Executable semantic layer (views are real SQL)
- ✅ Self-verifying (only valid views persist)
- ✅ Learning from failures (feedback loop)
- ✅ Encapsulates complex joins
- ✅ Reusable abstractions
- ✅ GraphRAG provides relationship discovery

**Weaknesses**:
- ❌ High complexity (3 agent pipeline + orchestration)
- ❌ Slow generation (minutes per view)
- ❌ Database modification required (creates actual views)
- ❌ Schema changes may break views
- ❌ View maintenance burden
- ❌ Requires DBA permissions

**When to Use**:
- Complex schemas with many joins
- Stable database schemas (not rapidly changing)
- Need for verified, executable abstractions
- Have time for iterative refinement

**Implementation Effort**: **6-8 weeks**
- Week 1-2: Build planner/critic/verifier agents
- Week 3-4: Implement feedback loop and view storage
- Week 5-6: GraphRAG integration
- Week 7-8: Testing and refinement

**Expected Accuracy**: **90-95%**
- Verified views eliminate join errors
- Critic ensures quality
- Feedback loop improves over time

**Cost**:
- Generation: ~$5-10 per database (many LLM calls for refinement)
- Per query: Lower (simpler SQL from views)
- Maintenance: High (view upkeep)

---

## Strategy 2: Ontology-Backed Virtualization

### Architecture

```
Schema → Ontology Mapper → Domain Ontology (RDF/OWL)
              ↓
    Multiple Semantic Projections:
    - Prompt Snippets
    - API Documentation
    - Data Catalog Entries
    - Business Glossary
              ↓
Question → Match to Ontology Concepts → Generate SQL via Rules
```

**Key Components**:
1. **Domain Ontology**: Formal representation of business concepts (RDF/OWL)
2. **Ontology Mapper**: Maps raw schema to ontology concepts
3. **Rule Engine**: Transforms ontology queries to SQL
4. **Projection Generator**: Creates different views from same ontology
5. **Harmonization Layer**: Ensures consistent terminology across outputs

### Example

**Ontology Definition** (simplified):
```turtle
@prefix wta: <http://example.org/wta#> .
@prefix sport: <http://example.org/sport#> .

wta:Player a sport:Athlete ;
  sport:hasAttribute wta:firstName, wta:countryCode ;
  sport:participatesIn wta:Match .

wta:Match a sport:Event ;
  sport:hasWinner wta:Player ;
  sport:hasLoser wta:Player ;
  sport:occursAt wta:Tournament .

wta:Tournament a sport:Competition ;
  sport:hasName wta:tourneyName .
```

**Mapping to Schema**:
```yaml
wta:Player → players table
  wta:firstName → players.first_name
  wta:countryCode → players.country_code

wta:Match → matches table
  wta:hasWinner → matches.winner_id
  wta:hasLoser → matches.loser_id
```

**Projections**:

1. **Prompt Snippet**:
```
Player: An athlete who competes in tennis tournaments
  - Attributes: firstName (athlete's given name), countryCode (nationality)
  - Participates in: Match (tennis matches)
```

2. **API Documentation**:
```json
{
  "entity": "Player",
  "type": "Athlete",
  "fields": {
    "firstName": {"type": "string", "meaning": "athlete's given name"},
    "countryCode": {"type": "string", "meaning": "nationality"}
  }
}
```

3. **SQL Generation Rule**:
```
Query: "Which players from USA won matches?"
Ontology Query: ?player a wta:Player ; wta:countryCode "USA" ; sport:participatesIn ?match ; sport:hasWinner ?player
SQL Translation: SELECT first_name FROM players WHERE country_code = 'USA' AND player_id IN (SELECT winner_id FROM matches)
```

### Characteristics

**Strengths**:
- ✅ Single source of truth (ontology)
- ✅ Consistent terminology across all outputs
- ✅ Multiple projections from one definition
- ✅ Auditable transformations
- ✅ Formal semantics (machine-readable)
- ✅ Standards-compliant (RDF/OWL)
- ✅ Enterprise-grade (widely used in compliance/healthcare)

**Weaknesses**:
- ❌ Very high complexity (ontology engineering expertise required)
- ❌ Steep learning curve (RDF, OWL, SPARQL)
- ❌ Slow iteration (ontology changes are heavyweight)
- ❌ Overkill for simple schemas
- ❌ Limited LLM support for ontologies
- ❌ Rule engine complexity

**When to Use**:
- Multi-domain data integration
- Compliance-heavy industries (healthcare, finance)
- Need for formal semantics
- Multiple consumer types (APIs, prompts, catalogs)
- Long-term strategic investment

**Implementation Effort**: **3-6 months**
- Month 1-2: Ontology design and mapping
- Month 3-4: Rule engine and SQL translation
- Month 5-6: Projection generators and testing

**Expected Accuracy**: **95%+**
- Formal semantics eliminate ambiguity
- Deterministic SQL generation
- No retrieval variability

**Cost**:
- Generation: Very high upfront (ontology engineering)
- Per query: Low (rule-based translation)
- Maintenance: High (ontology evolution)

---

## Strategy 3: Metric-Centric Semantic Hub

### Architecture

```
Schema → Metric Catalog Definition
              ↓
    Canonical Business Metrics + KPIs
    (Logical Layer - LLM Target)
              ↓
Question → Match to Metrics → Deterministic SQL Mapping
              ↓
    Execution-Based Gating (Validate Before Exposing)
```

**Key Components**:
1. **Metric Catalog**: Curated list of business metrics and KPIs
2. **Logical Tables**: Abstract business concepts (e.g., "Customer Lifetime Value")
3. **SQL Mappings**: Deterministic translation from metric to warehouse SQL
4. **Execution Gate**: Validates each metric definition before exposing
5. **LLM Abstraction**: LLM targets metrics, not raw schema

### Example

**Metric Catalog**:
```yaml
metrics:
  - id: player_win_rate
    name: "Player Win Rate"
    description: "Percentage of matches won by a player"
    logical_query: "SELECT player_id, (wins / total_matches) as win_rate FROM player_stats"
    sql_mapping: |
      SELECT
        p.player_id,
        p.first_name,
        COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END)::float /
        COUNT(m.match_num) as win_rate
      FROM players p
      JOIN matches m ON p.player_id IN (m.winner_id, m.loser_id)
      GROUP BY p.player_id, p.first_name
    validation_query: "SELECT * FROM player_win_rate LIMIT 1"
    gated: true  # Only expose if validation passes

  - id: tournament_match_count
    name: "Tournament Match Count"
    description: "Number of matches in each tournament"
    logical_query: "SELECT tournament_name, match_count FROM tournament_stats"
    sql_mapping: |
      SELECT
        t.tourney_name as tournament_name,
        COUNT(m.match_num) as match_count
      FROM tournaments t
      JOIN matches m ON t.tourney_id = m.tourney_id
      GROUP BY t.tourney_name
    validation_query: "SELECT * FROM tournament_match_count LIMIT 1"
    gated: true
```

**Usage**:
1. **Question**: "What is the win rate for players from France?"
2. **LLM matches to metric**: `player_win_rate`
3. **Logical query**: `SELECT * FROM player_win_rate WHERE country = 'France'`
4. **Deterministic mapping**: Inject stored SQL mapping + filter
5. **Final SQL**:
```sql
SELECT
  p.player_id,
  p.first_name,
  COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END)::float /
  COUNT(m.match_num) as win_rate
FROM players p
JOIN matches m ON p.player_id IN (m.winner_id, m.loser_id)
WHERE p.country_code = 'FRA'
GROUP BY p.player_id, p.first_name
```

**Execution Gating**:
- Before exposing metric `player_win_rate`, run validation query
- If validation passes → expose to LLM
- If validation fails → hide metric, log error
- **Guarantees**: Every metric improves accuracy (no broken chunks)

### Characteristics

**Strengths**:
- ✅ Shields LLM from complex joins
- ✅ Deterministic SQL generation (no LLM interpretation errors)
- ✅ Consistent metric definitions
- ✅ Execution-gated (only working metrics exposed)
- ✅ Business-friendly abstractions
- ✅ Easier for analysts to define metrics
- ✅ Handles schema changes gracefully (update mappings centrally)

**Weaknesses**:
- ❌ Requires upfront metric definition
- ❌ Manual curation needed
- ❌ Limited to predefined metrics
- ❌ May not handle ad-hoc queries well
- ❌ Maintenance burden (metric catalog upkeep)

**When to Use**:
- Analytics/BI use cases
- Stable set of business metrics
- Need for consistent KPI definitions
- Complex join patterns to abstract away
- Multi-user environments (prevent join errors)

**Implementation Effort**: **4-8 weeks**
- Week 1-2: Metric catalog schema and storage
- Week 3-4: SQL mapping engine
- Week 5-6: Execution gating and validation
- Week 7-8: LLM integration and testing

**Expected Accuracy**: **90-93%**
- Deterministic SQL eliminates interpretation errors
- Execution gating ensures quality
- Limited to predefined metrics (may miss edge cases)

**Cost**:
- Generation: Medium (manual metric definition)
- Per query: Low (deterministic mapping)
- Maintenance: Medium-High (catalog upkeep)

---

## Detailed Comparison Matrix

### By Dimension

| Dimension | Current (RAG) | Multi-Agent | Ontology | Metric Hub |
|-----------|---------------|-------------|----------|------------|
| **Architecture Complexity** | Low | High | Very High | Medium-High |
| **Implementation Time** | 1 week | 6-8 weeks | 3-6 months | 4-8 weeks |
| **Accuracy Potential** | 85-87% | 90-95% | 95%+ | 90-93% |
| **Maintenance Burden** | Low | Medium | High | Medium-High |
| **Schema Change Impact** | Low (live schema) | High (views break) | Medium (remap) | Medium (update mappings) |
| **Flexibility** | High (any query) | High (any query) | Medium (ontology coverage) | Medium (defined metrics) |
| **Database Modification** | None | Yes (creates views) | None | None |
| **LLM Dependency** | High | High | Low | Medium |
| **Determinism** | Low (retrieval varies) | Medium (verified views) | High (rule-based) | High (mappings) |
| **Cost per Query** | $0.000675 | $0.0004 | $0.0003 | $0.0004 |
| **Generation Cost** | $0.003/db | $5-10/db | $100+/db | $1-2/db |
| **Learning from Failures** | No | Yes | No | No |
| **Best for Ad-hoc Queries** | Yes | Yes | No | No |
| **Best for Analytics/BI** | Medium | Medium | High | Very High |
| **Best for Rapid Iteration** | Very High | Low | Very Low | Medium |

### By Use Case

| Use Case | Recommended Strategy | Rationale |
|----------|---------------------|-----------|
| **General Text-to-SQL (Spider)** | Current (RAG) | Flexible, handles diverse schemas, rapid iteration |
| **Production Text-to-SQL** | Metric Hub → Multi-Agent | Start with hub for common queries, add multi-agent for coverage |
| **Enterprise Data Catalog** | Ontology | Formal semantics, multi-domain, compliance |
| **BI/Analytics Platform** | Metric Hub | Consistent KPIs, shields users from joins |
| **Research/Prototyping** | Current (RAG) | Fast iteration, low cost, easy to modify |
| **Complex Schema (50+ tables)** | Multi-Agent | Views encapsulate complexity |
| **Regulated Industry** | Ontology | Auditable, standards-compliant |
| **Multi-tenant SaaS** | Current (RAG) | No schema modification, works with any DB |

---

## Evolution Path Recommendation

### Phase 0: Current State (RAG-based)
**Status**: ✅ Implemented + Phase 1 improvements
**Accuracy**: 84-86% (expected)
**Next**: Run benchmark to validate Phase 1

### Phase 1-2: Incremental RAG Improvements (Now)
**Status**: 🔄 In progress
**Actions**:
- ✅ Increase retrieval 5→10
- ✅ Chunk type weighting
- ✅ Metadata limit 1000→2000
- ⏳ Table detection force retrieval
- ⏳ Remove ambiguities chunks

**Target**: 85-87% accuracy
**Timeline**: 1-2 weeks
**Decision Point**: If ≥85%, stop here. If <85%, proceed to Phase 3.

### Phase 3: Metric-Centric Hub Pilot (Next Major Evolution)
**Status**: 🔮 Future (if needed)
**Why This Strategy?**
1. **Moderate complexity** (4-8 weeks vs 3-6 months for ontology)
2. **High accuracy potential** (90-93%)
3. **Production-ready** (deterministic, validated)
4. **Natural fit for Spider** (many queries are KPI-style: "how many", "what is the average")
5. **No database modification** (unlike Multi-Agent views)

**Pilot Approach**:
1. Choose 2-3 databases (e.g., wta_1, concert_singer)
2. Define top 10 metrics per database
3. Build metric catalog + mapping engine
4. Test on subset of queries
5. Measure accuracy improvement
6. If successful, expand to all databases

**Timeline**: 4-6 weeks
**Expected Impact**: +3-5% accuracy (87% → 90-92%)

### Phase 4: Multi-Agent Refinement (Optional)
**Status**: 🔮 Future (if Metric Hub insufficient)
**When to Use**: If metric hub coverage is insufficient for ad-hoc queries
**Hybrid Approach**:
- Metric hub for common KPIs
- Multi-agent views for complex joins
- RAG for edge cases

**Timeline**: 8-12 weeks
**Expected Impact**: +2-3% accuracy (90% → 92-95%)

### Phase 5: Ontology (Long-term Strategic)
**Status**: 🔮 Future (production hardening)
**When to Use**: If productionizing for enterprise with compliance needs
**Timeline**: 6-12 months
**Expected Impact**: Formalization, multi-domain support, auditability

---

## Recommendation: Hybrid Approach

### Immediate (Now)
**Continue with Current (RAG) + Phase 1-2 Improvements**
- ✅ Low risk, high ROI
- ✅ 1-2 weeks to 85-87% accuracy
- ✅ Validates retrieval improvements before bigger investment

### Short-term (1-2 months)
**Pilot Metric-Centric Hub on 2-3 Databases**
- Select databases with clear KPIs (wta_1, concert_singer, student_transcripts)
- Define 10-20 core metrics
- Build minimal viable metric catalog
- A/B test: RAG vs Metric Hub
- **Decision**: If >3% improvement, expand to all databases

### Medium-term (3-6 months)
**Expand Metric Hub + Selective Multi-Agent**
- Full metric catalog for all databases
- Multi-agent views for consistently problematic joins
- RAG fallback for unmatched queries
- **Target**: 90-93% accuracy

### Long-term (6-12 months)
**Evaluate Ontology for Production Hardening**
- Only if enterprise deployment with compliance needs
- Formalize metric definitions in ontology
- Multi-domain support
- Standards-compliant

---

## Key Insights

### What We've Learned from Current Approach

**Successes**:
1. ✅ Live schema as ground truth works well
2. ✅ Removing redundancy (schema, glossaries) improves accuracy
3. ✅ Retrieval quality matters more than semantic layer content
4. ✅ Table-specific context beats generic documentation

**Failures**:
1. ❌ Only 20-40% of retrieved chunks are highly relevant
2. ❌ Generic chunks (overview, guidelines) waste slots
3. ❌ Missing critical tables (e.g., 'matches' in wta_1)
4. ❌ No verification of semantic layer accuracy

### Why Metric Hub is the Best Next Step

1. **Addresses retrieval problem**: Metrics are inherently relevant (no generic chunks)
2. **Execution-gated**: Only expose validated metrics (no broken chunks)
3. **Deterministic**: No LLM interpretation errors in SQL generation
4. **Scalable**: Works for 20 databases or 200 databases
5. **Maintainable**: Analysts can define metrics without code changes
6. **Natural fit**: Spider queries are often KPI-style

### Why NOT Multi-Agent or Ontology (Yet)

**Multi-Agent**:
- ⚠️ Creates database views (schema modification)
- ⚠️ Fragile to schema changes
- ⚠️ Requires DBA permissions
- ⚠️ 6-8 week investment before seeing results
- ✅ Save for later if metric hub insufficient

**Ontology**:
- ⚠️ 3-6 month investment
- ⚠️ Requires specialized expertise
- ⚠️ Overkill for research prototype
- ⚠️ Limited LLM support
- ✅ Save for production hardening (if ever needed)

---

## Conclusion

**For QueryDawg thesis project:**

1. **Now**: Complete Phase 1-2 RAG improvements (target: 85-87%)
2. **Next**: Pilot Metric Hub on 2-3 databases (target: 90-92%)
3. **Later**: Multi-Agent if needed for coverage
4. **Much Later**: Ontology if productionizing for enterprise

**The metric-centric hub is the sweet spot**: moderate complexity, high accuracy, production-ready, and a natural evolution from current RAG approach.

**Key Principle**: Incremental evolution beats revolutionary change. Each step validates assumptions and builds on previous work.
