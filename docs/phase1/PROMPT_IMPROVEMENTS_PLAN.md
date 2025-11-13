# Prompt Improvements Implementation Plan

**Date**: 2025-11-03
**Goal**: Improve enhanced prompt accuracy from 80.9% to 85-87% (beating baseline's 83.2%)
**Current Issues**: Wrong chunks retrieved, content truncation, poor chunk relevance

## Summary of Improvements

| Priority | Improvement | Expected Impact | Complexity | Est. Time |
|----------|-------------|-----------------|------------|-----------|
| HIGH | Increase retrieval 5→10 | +2-3% | Low | 15 min |
| HIGH | Chunk type weighting | +1-2% | Medium | 1-2 hours |
| HIGH | Increase metadata limit 1000→2000 | +0.5-1% | Low | 15 min |
| MEDIUM | Table detection force retrieval | +1-2% | Medium | 2-3 hours |
| MEDIUM | Remove ambiguities chunks | +0.5% | Low | 30 min |
| LOW | Hybrid retrieval | +1-2% | High | 4-6 hours |
| LOW | Re-ranking with cross-encoder | +1-2% | High | 4-6 hours |

**Total Expected Impact**: +6-12% accuracy improvement
**Recommended Approach**: Implement HIGH priority first, test, then proceed to MEDIUM

---

## Phase 1: HIGH PRIORITY (Quick Wins)

### 1.1 Increase Chunk Retrieval (5 → 10)

**Problem**: Missing critical tables in retrieval (e.g., dev_0451 missing 'matches' table)

**Expected Impact**: +2-3% accuracy

**Files to Modify**:
- `backend/app/services/embedding_service.py`

**Implementation**:

```python
# File: backend/app/services/embedding_service.py
# Current: Line ~245-250 (in search_semantic_layer method)

def search_semantic_layer(
    self,
    question: str,
    database_name: str,
    top_k: int = 5  # CHANGE THIS
) -> List[Dict[str, Any]]:
```

**Change to**:
```python
def search_semantic_layer(
    self,
    question: str,
    database_name: str,
    top_k: int = 10  # Changed from 5 to 10
) -> List[Dict[str, Any]]:
```

**Also update callers**:
- `backend/app/services/sql_generator.py` (likely around line 100-150)
- Search for all calls to `search_semantic_layer()` and update `top_k` parameter

**Testing**:
1. Run test on dev_0451: Should now retrieve 'matches' table
2. Check prompt length doesn't exceed model limits (~8k tokens safe for GPT-4o-mini)
3. Verify all 10 chunks fit within context window

**Rollback**: Change `top_k` back to 5

**Risk**: LOW - Just retrieving more context, won't break anything

---

### 1.2 Implement Chunk Type Weighting

**Problem**: Generic chunks (overview, ambiguities, guidelines) ranking too high, pushing out specific table docs

**Expected Impact**: +1-2% accuracy

**Files to Modify**:
- `backend/app/services/embedding_service.py`

**Implementation Strategy**:

Add a weighting system that boosts/penalizes chunks based on type:

```python
# File: backend/app/services/embedding_service.py
# Add after search_semantic_layer method (around line 260)

CHUNK_TYPE_WEIGHTS = {
    'table': 1.2,           # BOOST table-specific docs (most valuable)
    'cross_table_patterns': 1.1,  # BOOST multi-table patterns
    'overview': 0.7,        # PENALIZE generic overviews
    'ambiguities': 0.6,     # PENALIZE ambiguities (being removed anyway)
    'guidelines': 0.8,      # PENALIZE generic guidelines
    'glossary': 0.5         # PENALIZE glossaries (being removed anyway)
}

def search_semantic_layer(
    self,
    question: str,
    database_name: str,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """Search semantic layer with chunk type weighting"""

    # Get embedding
    question_embedding = self._get_embedding(question)

    # Query Pinecone (get more than top_k to allow re-ranking)
    results = self.index.query(
        vector=question_embedding,
        filter={"database": database_name},
        top_k=top_k * 2,  # Get 2x more results for re-ranking
        include_metadata=True
    )

    # Re-rank with weights
    weighted_results = []
    for match in results['matches']:
        chunk_type = match['metadata'].get('chunk_type', 'unknown')
        weight = CHUNK_TYPE_WEIGHTS.get(chunk_type, 1.0)

        # Apply weight to similarity score
        weighted_score = match['score'] * weight

        weighted_results.append({
            'score': weighted_score,
            'original_score': match['score'],
            'chunk_type': chunk_type,
            'text': match['metadata'].get('text', ''),
            'metadata': match['metadata']
        })

    # Sort by weighted score and take top_k
    weighted_results.sort(key=lambda x: x['score'], reverse=True)
    return weighted_results[:top_k]
```

**Testing**:
1. Test on dev_0451: Verify 'matches' table now appears in top 10
2. Check that overview/guidelines don't dominate results
3. Run on 5-10 sample queries, inspect retrieved chunks

**Rollback**: Remove weighting logic, return to vanilla vector search

**Risk**: MEDIUM - Could over-boost wrong chunks, needs tuning

**Tuning Strategy**:
- Start with conservative weights (1.2, 0.8)
- Run benchmark on 100 questions
- Adjust weights based on results

---

### 1.3 Increase Metadata Limit (1000 → 2000 chars)

**Problem**: Content truncation cutting off valuable context mid-sentence

**Expected Impact**: +0.5-1% accuracy

**Files to Modify**:
- `backend/app/services/embedding_service.py`

**Implementation**:

```python
# File: backend/app/services/embedding_service.py
# Find all occurrences of text truncation (likely around line 100-200 in chunking methods)

# Current (example from _chunk_table_doc):
text = "\n".join(text_parts)
if len(text) > 1000:
    text = text[:1000] + "..."

# Change to:
text = "\n".join(text_parts)
if len(text) > 2000:
    text = text[:2000] + "..."
```

**Search for all truncation points**:
```bash
grep -n "text\[:1000\]" backend/app/services/embedding_service.py
```

**Update all instances to 2000**

**Testing**:
1. Check Pinecone metadata limits (should support 40KB, 2000 is safe)
2. Verify no truncation in typical table docs
3. Check embedding costs don't spike (2x longer text = 2x cost)

**Rollback**: Change back to 1000

**Risk**: LOW - Just storing more metadata

**Cost Impact**: Minimal (metadata is cheap, embeddings are based on chunk text not metadata)

---

## Phase 2: MEDIUM PRIORITY (Targeted Improvements)

### 2.1 Table Detection Force Retrieval

**Problem**: Questions mention specific tables (e.g., "players" and "matches") but only retrieve one

**Expected Impact**: +1-2% accuracy

**Files to Modify**:
- `backend/app/services/embedding_service.py`
- `backend/app/services/sql_generator.py`

**Implementation Strategy**:

```python
# File: backend/app/services/embedding_service.py
# Add new method

import re

def detect_table_names(self, question: str, database_name: str) -> List[str]:
    """
    Detect potential table names mentioned in the question.

    Uses fuzzy matching against actual table names in the database.
    """
    # Get all table names for this database from schema
    # This requires schema extractor access
    from ..database.supabase_schema_extractor import SupabaseSchemaExtractor

    extractor = SupabaseSchemaExtractor(self.database_url)
    schema = extractor.extract_schema(database_name)
    table_names = [t['name'] for t in schema['tables']]

    # Look for table name mentions (plural forms, partial matches)
    question_lower = question.lower()
    detected = []

    for table_name in table_names:
        # Check exact match
        if table_name.lower() in question_lower:
            detected.append(table_name)
            continue

        # Check singular/plural variations
        # e.g., "player" matches "players" table
        if table_name.endswith('s') and table_name[:-1].lower() in question_lower:
            detected.append(table_name)
        elif f"{table_name}s".lower() in question_lower:
            detected.append(table_name)

    return detected

def search_semantic_layer_with_table_boost(
    self,
    question: str,
    database_name: str,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Search semantic layer and force-include chunks for detected tables.
    """
    # Detect table names
    detected_tables = self.detect_table_names(question, database_name)

    # Get semantic chunks from vector search
    semantic_chunks = self.search_semantic_layer(question, database_name, top_k=top_k)

    # Check which detected tables are missing
    retrieved_tables = set()
    for chunk in semantic_chunks:
        if chunk['metadata'].get('chunk_type') == 'table':
            retrieved_tables.add(chunk['metadata'].get('table_name'))

    missing_tables = [t for t in detected_tables if t not in retrieved_tables]

    # Force-retrieve missing table chunks
    if missing_tables:
        for table_name in missing_tables[:3]:  # Limit to 3 forced retrievals
            # Query Pinecone for this specific table
            table_chunk = self.index.query(
                vector=self._get_embedding(f"table {table_name}"),
                filter={
                    "database": database_name,
                    "chunk_type": "table",
                    "table_name": table_name
                },
                top_k=1,
                include_metadata=True
            )

            if table_chunk['matches']:
                # Insert at position based on relevance
                forced_chunk = {
                    'score': 0.9,  # High score to ensure inclusion
                    'forced': True,
                    'text': table_chunk['matches'][0]['metadata'].get('text', ''),
                    'metadata': table_chunk['matches'][0]['metadata']
                }
                semantic_chunks.insert(len(detected_tables), forced_chunk)

    # Trim back to top_k
    return semantic_chunks[:top_k]
```

**Update caller**:
```python
# File: backend/app/services/sql_generator.py
# Change from search_semantic_layer to search_semantic_layer_with_table_boost

chunks = self.embedding_service.search_semantic_layer_with_table_boost(
    question=question,
    database_name=database_name,
    top_k=10
)
```

**Testing**:
1. Test on dev_0451: Should force-retrieve 'matches' table
2. Test on questions mentioning multiple tables
3. Verify forced chunks are relevant

**Rollback**: Revert to `search_semantic_layer` without table detection

**Risk**: MEDIUM - Could force-retrieve wrong tables if detection is inaccurate

---

### 2.2 Remove Ambiguities Chunks

**Problem**: Like glossaries, ambiguities add noise without much value

**Expected Impact**: +0.5% accuracy

**Files to Modify**:
- `backend/app/services/embedding_service.py`

**Implementation**:

Simply comment out or delete the ambiguities chunking code:

```python
# File: backend/app/services/embedding_service.py
# Find _chunk_ambiguities method (likely around line 200-220)

def chunk_semantic_layer(self, semantic_layer: Dict[str, Any], database_name: str) -> List[Dict[str, Any]]:
    """Create chunks from semantic layer"""
    chunks = []

    # Overview
    chunks.append(self._chunk_overview(semantic_layer, database_name))

    # Tables
    for table in semantic_layer.get('tables', []):
        chunks.append(self._chunk_table_doc(table, database_name))

    # Cross-table patterns
    if semantic_layer.get('cross_table_patterns'):
        chunks.append(self._chunk_patterns(semantic_layer, database_name))

    # Guidelines
    if semantic_layer.get('query_guidelines'):
        chunks.append(self._chunk_guidelines(semantic_layer, database_name))

    # REMOVE THIS:
    # if semantic_layer.get('ambiguities'):
    #     chunks.append(self._chunk_ambiguities(semantic_layer, database_name))

    return chunks
```

**Also delete the `_chunk_ambiguities` method**

**Testing**:
1. Regenerate embeddings for 1 database
2. Verify ambiguities chunks no longer exist
3. Check retrieval quality improves

**Rollback**: Uncomment the code

**Risk**: LOW - Ambiguities were rarely useful

---

## Phase 3: LOW PRIORITY (Advanced Features)

### 3.1 Hybrid Retrieval (Keyword + Vector)

**Problem**: Vector search misses exact keyword matches (e.g., table names)

**Expected Impact**: +1-2% accuracy

**Complexity**: HIGH - Requires BM25 index or Pinecone sparse-dense hybrid

**Implementation Options**:

**Option A: Pinecone Hybrid Search** (Recommended if available)
```python
# Pinecone supports sparse-dense hybrid as of 2024
results = self.index.query(
    vector=dense_embedding,
    sparse_vector={
        'indices': keyword_indices,
        'values': keyword_weights
    },
    top_k=10,
    alpha=0.7  # Weight towards dense (0.5 = equal)
)
```

**Option B: Dual Retrieval + Merge**
```python
from rank_bm25 import BM25Okapi

# Get vector results
vector_results = self.search_semantic_layer(question, database_name, top_k=20)

# Get BM25 results (requires local index)
bm25_results = self.bm25_search(question, database_name, top_k=20)

# Merge with reciprocal rank fusion
merged = self.reciprocal_rank_fusion(vector_results, bm25_results, k=10)
```

**Files to Modify**:
- `backend/app/services/embedding_service.py`
- May need to add BM25 index building during embedding

**Testing**:
- Test on keyword-heavy queries (table names, specific column values)
- Compare to pure vector search

**Risk**: HIGH - Complex implementation, may not improve much

---

### 3.2 Re-ranking with Cross-Encoder

**Problem**: Bi-encoder (embeddings) gives coarse relevance, cross-encoder gives fine-grained

**Expected Impact**: +1-2% accuracy

**Implementation**:

```python
from sentence_transformers import CrossEncoder

class EmbeddingService:
    def __init__(self, ...):
        # Add cross-encoder
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def search_with_reranking(
        self,
        question: str,
        database_name: str,
        top_k: int = 10
    ):
        # Get top 50 candidates from vector search
        candidates = self.search_semantic_layer(question, database_name, top_k=50)

        # Re-rank with cross-encoder
        pairs = [[question, chunk['text']] for chunk in candidates]
        scores = self.cross_encoder.predict(pairs)

        # Sort by cross-encoder scores
        for i, chunk in enumerate(candidates):
            chunk['rerank_score'] = scores[i]

        candidates.sort(key=lambda x: x['rerank_score'], reverse=True)
        return candidates[:top_k]
```

**Cost**: Cross-encoder inference is ~10x slower than embeddings

**Files to Modify**:
- `backend/app/services/embedding_service.py`
- Add cross-encoder model to requirements.txt

**Testing**:
- Compare re-ranked results to vanilla vector search
- Measure latency impact (should be <200ms for 50 candidates)

**Risk**: MEDIUM - Adds latency, may not improve much

---

## Implementation Order (Recommended)

### Week 1: Quick Wins
1. **Day 1**: Implement 1.1 (increase retrieval) + 1.3 (metadata limit)
   - Test on 10 sample queries
   - Push to Railway, run small benchmark (100 questions)

2. **Day 2**: Implement 1.2 (chunk weighting)
   - Test weighting values
   - Tune based on results

3. **Day 3**: Implement 2.2 (remove ambiguities)
   - Regenerate embeddings for 2-3 databases
   - Test retrieval quality

4. **Day 4-5**: Run full benchmark
   - Measure impact: Should be at 84-86% (baseline is 83.2%)
   - **DECISION POINT**: If at 85%+, STOP HERE. If not, continue to Phase 2.

### Week 2: Targeted Improvements (if needed)
5. **Day 6-8**: Implement 2.1 (table detection)
   - Build and test detection logic
   - Test on queries with multiple tables

6. **Day 9-10**: Run full benchmark
   - Measure impact: Should be at 86-87%
   - **DECISION POINT**: If at 86%+, STOP HERE. If not, consider Phase 3.

### Week 3+: Advanced Features (optional)
7. Implement 3.1 or 3.2 if still not hitting targets

---

## Testing Strategy

### Unit Tests
```python
# tests/test_embedding_service.py

def test_chunk_weighting():
    """Verify table chunks rank higher than overview"""
    service = EmbeddingService(...)
    results = service.search_semantic_layer(
        question="How many players are there?",
        database_name="wta_1",
        top_k=10
    )

    # First result should be 'players' table doc
    assert results[0]['metadata']['chunk_type'] == 'table'
    assert results[0]['metadata']['table_name'] == 'players'

def test_table_detection():
    """Verify table names are detected in questions"""
    service = EmbeddingService(...)
    tables = service.detect_table_names(
        question="What players won matches?",
        database_name="wta_1"
    )

    assert 'players' in tables
    assert 'matches' in tables
```

### Integration Tests
```python
def test_end_to_end_with_improvements():
    """Test full SQL generation with improved retrieval"""
    generator = SQLGenerator(...)

    result = generator.generate_sql(
        question="What are the country code and first name of the players who won in both tourney WTA Championships and Australian Open?",
        database_name="wta_1",
        use_semantic_layer=True
    )

    # Should retrieve 'matches' table
    assert 'matches' in result['semantic_context']
    # Should use correct columns
    assert 'tourney_name' in result['generated_sql']
    assert 'tourney_id' not in result['generated_sql']
```

### Benchmark Tests
```bash
# Run on subset for quick validation
python scripts/run_benchmark.py --databases wta_1,concert_singer --limit 50

# Run full benchmark for final validation
python scripts/run_benchmark.py --full
```

---

## Rollback Strategy

### Quick Rollback (if things break)
1. **Git revert**: Each phase should be a separate commit
   ```bash
   git log --oneline  # Find commit to revert
   git revert <commit-hash>
   git push
   ```

2. **Feature flags**: Add config to enable/disable improvements
   ```python
   # backend/app/config.py
   class Config:
       CHUNK_WEIGHTING_ENABLED = os.getenv('CHUNK_WEIGHTING_ENABLED', 'true') == 'true'
       TABLE_DETECTION_ENABLED = os.getenv('TABLE_DETECTION_ENABLED', 'true') == 'true'
       TOP_K_CHUNKS = int(os.getenv('TOP_K_CHUNKS', '10'))
   ```

3. **A/B testing**: Run both old and new in parallel, compare results

### Monitoring
- Track accuracy after each change
- If accuracy drops >1%, rollback immediately
- If accuracy improves <0.5%, reconsider the change

---

## Success Metrics

### Phase 1 Success Criteria
- Enhanced accuracy: 84-86% (up from 80.9%)
- Beats baseline: 83.2%
- Prompt length: <8000 tokens
- No increase in errors

### Phase 2 Success Criteria
- Enhanced accuracy: 86-87%
- Beats baseline by 3-4%
- Table detection accuracy: >90%

### Phase 3 Success Criteria
- Enhanced accuracy: 87-89%
- Beats baseline by 4-6%
- Latency: <2 seconds per query

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Retrieval quality degrades | Low | High | A/B test before full deployment |
| Context window exceeded | Low | Medium | Monitor prompt lengths, cap at 8k tokens |
| Costs increase significantly | Low | Medium | Monitor token usage, set alerts |
| Improvements don't materialize | Medium | Medium | Implement incrementally, measure each step |
| Latency increases | Low | Low | Profile performance, optimize hotspots |

---

## Cost Impact

### Current Costs (Estimated)
- Baseline: ~1500 tokens/query × $0.15/1M tokens = $0.000225/query
- Enhanced: ~3000 tokens/query × $0.15/1M tokens = $0.00045/query

### After Improvements
- Enhanced: ~4500 tokens/query (10 chunks vs 5) = $0.000675/query
- **Increase: +50% cost** ($0.00045 → $0.000675)

### Cost-Benefit
- Accuracy gain: +5-7%
- Cost increase: +$0.000225 per query
- **For 10,000 queries**: +$2.25 cost for 500-700 more correct answers
- **Worth it if accuracy matters more than cost**

---

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Get approval** for Phase 1 implementation
3. **Create feature branch**: `git checkout -b prompt-improvements`
4. **Implement Phase 1.1** (increase retrieval)
5. **Test and measure** before proceeding

**Estimated Timeline**:
- Phase 1: 3-5 days (including testing)
- Phase 2: 5-7 days (if needed)
- Total: 1-2 weeks to reach 85%+ accuracy

**Success Target**: Enhanced accuracy at 85-87%, beating baseline by 2-4%
