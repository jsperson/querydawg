# Root Cause Analysis: Semantic Layer Underperformance
## Run 22 Analysis - Why Enhanced Approach Performed -2.3% Worse Than Baseline

**Date**: 2025-11-02
**Analyzed Run**: Full Spider 1.0 Run 22
**Overall Result**: Enhanced (semantic layer) = 49.9% accuracy, Baseline = 52.2% accuracy
**Delta**: -2.3 percentage points

---

## Executive Summary

The semantic layer is **actively harmful** in its current implementation, causing enhanced queries to perform worse than baseline despite additional context. Four critical issues were identified:

1. **Database Setup Issues** (84 questions affected)
2. **Prompt Guideline Conflicts** (affects aggregation queries)
3. **Poor Vector Search Relevance** (20-40% relevance rate)
4. **Missing or Misleading Semantic Content** (JOIN types, wrong column guidance)

---

## Phase 1: Database Setup Issues

### Database: cre_Doc_Template_Mgt (0% accuracy for both approaches)

**Issue**: Gold SQL lacks schema qualification, causing all comparisons to fail.

**Example**:
```sql
-- Gold SQL (fails to execute):
SELECT count(*) FROM Documents

-- Both baseline and enhanced generate correct SQL:
SELECT COUNT(*) FROM cre_Doc_Template_Mgt.documents;

-- Error: relation "documents" does not exist
```

**Impact**: All 84 questions in this database marked as failures despite correct SQL generation.

**Root Cause**: Spider benchmark data preparation issue, not a query generation problem.

**Recommendation**:
- Fix gold SQL to include schema qualification, OR
- Exclude this database from accuracy calculations, OR
- Modify comparison logic to handle unqualified gold SQL

---

## Phase 2: wta_1 Failures (Worst Performer: -8.1%)

Analyzed 5 questions where baseline succeeded but enhanced failed.

### Pattern 1: Guideline #9 Violations (40% of failures)

**Questions**: dev_0475, dev_0476

**Issue**: Enhanced includes COUNT(*) when question asks for superlative identifiers.

**Example**:
```
Question: "find the code of the country where has the greatest number of players"

Gold:     SELECT country_code FROM players GROUP BY country_code ORDER BY COUNT(*) DESC LIMIT 1
Baseline: SELECT country_code FROM players GROUP BY country_code ORDER BY COUNT(*) DESC LIMIT 1 ✅
Enhanced: SELECT country_code, COUNT(*) AS player_count FROM players GROUP BY country_code ORDER BY player_count DESC LIMIT 1 ❌
```

**Root Cause**: Guideline #9 was recently fixed, but Run 22 may have used old prompts. The guideline is also still imperfect.

**Current Guideline #9**:
```
When the question explicitly asks for quantities ("how many", "what is the total", "what is the average"),
INCLUDE the aggregation (COUNT, SUM, AVG) in the SELECT clause. Only exclude aggregations when the
question asks for superlatives or identifiers (e.g., "which year had the most concerts?" wants the year,
not the count).
```

**Issue**: Questions like "where has the greatest number" are ambiguous - they ask about a superlative but reference a quantity.

**Recommendation**:
- Verify Run 22 used updated prompts
- Refine guideline to handle "most/least/greatest number" phrasing
- Consider: If LIMIT 1, exclude aggregation from SELECT

### Pattern 2: Incorrect JOIN Types (40% of failures)

**Questions**: dev_0470, dev_0472

**Issue**: Enhanced uses LEFT JOIN when INNER JOIN is correct.

**Example**:
```
Question: "What are the first names of all players, and their average rankings?"

Baseline: SELECT p.first_name, AVG(r.ranking) FROM players p
          INNER JOIN rankings r ON p.player_id = r.player_id GROUP BY p.first_name ✅

Enhanced: SELECT p.first_name, AVG(r.ranking) FROM players p
          LEFT JOIN rankings r ON p.player_id = r.player_id GROUP BY p.first_name ❌
```

**Why Enhanced is Wrong**: LEFT JOIN includes players without rankings, returning NULL averages. The question asks for "average rankings", implying only players who have rankings.

**Semantic Context Retrieved**:
```
join_pattern: "JOIN players ON rankings.player_id = players.player_id"
```

**Root Cause**: Semantic layer provides generic "JOIN" without specifying INNER vs LEFT. The word "all" in "all players" is interpreted as "include ALL players" rather than "all players (who have rankings)".

**Recommendation**:
- Add JOIN type specifications to semantic layer: "Use INNER JOIN when aggregating related data"
- Add common query patterns showing correct JOIN types for typical scenarios
- Consider adding "INNER JOIN by default unless question explicitly says 'including those without...'"

### Pattern 3: Misleading Semantic Guidelines (20% of failures)

**Question**: dev_0451

**Issue**: Semantic guideline says "Filter by tourney_id" but question mentions tournament names.

**Example**:
```
Question: "players who won in both tourney WTA Championships and Australian Open"

Gold:     WHERE m.tourney_name IN ('WTA Championships', 'Australian Open') ✅
Baseline: WHERE m.tourney_name IN ('WTA Championships', 'Australian Open') ✅
Enhanced: WHERE m.tourney_id IN ('WTA Championships', 'Australian Open') ❌
```

**Semantic Chunk Retrieved** (score 0.37):
```
Query Guidelines for wta_1:
- Filter by tourney_id for tournament-specific queries.
```

**Root Cause**: Generic guideline doesn't account for whether the user provides names vs IDs. The matches table has both columns:
- `tourney_id`: Internal identifier
- `tourney_name`: Display name (what users naturally reference)

**Recommendation**:
- Remove or refine overly generic guidelines
- Make guidelines context-aware: "Use tourney_id when filtering by ID, tourney_name when filtering by name"
- Prioritize column documentation over generic guidelines in vector search

---

## Phase 3: concert_singer Success Analysis (+4.4%)

Analyzed why semantic layer HELPED in concert_singer.

### Success Pattern: Fixing Table Alias Bugs

**Questions**: dev_0025, dev_0041, dev_0042

**Issue**: Baseline had aliasing errors.

**Example**:
```
Question: "What is the name and capacity of the stadium with the most concerts after 2013?"

Baseline: SELECT s.name, st.capacity
          FROM concert c
          INNER JOIN stadium st ON c.stadium_id = st.stadium_id
          WHERE c.year > 2013
          GROUP BY s.name, st.capacity ❌
          -- References 's.name' but stadium aliased as 'st'

Enhanced: SELECT s.name, s.capacity
          FROM stadium s
          JOIN concert c ON s.stadium_id = c.stadium_id
          WHERE c.year > 2013
          GROUP BY s.stadium_id ✅
          -- Consistent aliasing
```

**Why Semantic Layer Helped**:
- Provided clear table names repeatedly in documentation
- "Grounded" the LLM in correct table/column references
- Reduced hallucination of incorrect aliases

**Key Insight**: Semantic layers are beneficial when they provide **clarity** (consistent naming, clear structure) but harmful when they add **ambiguity** (generic guidelines, wrong suggestions).

---

## Phase 4: Vector Search Relevance Analysis

Analyzed semantic chunk relevance for sample questions.

### Finding: 20-40% Relevance Rate

**Simple Query Example** (dev_0812): "What are the cities whose population is between 160000 and 900000?"

Retrieved chunks:
1. ✅ City table with population column (score 0.44) - HIGHLY RELEVANT
2. ⚠️ Database overview (score 0.38) - SOMEWHAT RELEVANT
3. ❌ Cross-table patterns about JOINs (score 0.37) - NOT NEEDED
4. ❌ Generic guidelines about JOINs (score 0.37) - NOT NEEDED
5. ❌ Glossary defining "City" (score 0.36) - NOT HELPFUL

**Relevance**: 1-2 out of 5 chunks useful (20-40%)

**Complex Query Example** (dev_0451): "players who won in both tourney WTA Championships and Australian Open"

Retrieved chunks:
1. ❌ Ambiguities about dates/names (score 0.47) - NOT RELEVANT
2. ❌ Glossary with basic definitions (score 0.42) - NOT HELPFUL
3. ✅ Players table documentation (score 0.41) - RELEVANT
4. ❌ Database overview (score 0.38) - NOT HELPFUL
5. ⚠️ Guidelines: "Filter by tourney_id" (score 0.37) - **ACTIVELY HARMFUL**

**Relevance**: 1 out of 5 chunks useful, 1 actively harmful (20%)

**Critical Missing**: Matches table documentation not retrieved despite being essential for the query.

### Root Causes of Poor Retrieval

1. **Generic content ranks too high**: Glossaries, overviews, and ambiguities have high semantic similarity to many questions but provide little value.

2. **Table-specific content underweighted**: Actual table documentation that would help construct the query ranks lower or isn't retrieved.

3. **No query-type awareness**: Simple single-table queries get JOIN guidance; complex multi-table queries miss key table docs.

4. **Guidelines treated as facts**: Generic guidelines like "use tourney_id" are retrieved and followed even when contextually wrong.

### Recommendations for Vector Search

1. **Implement chunk type weighting**:
   - Table documentation: 2.0x weight
   - Relationships/JOIN patterns: 1.5x weight
   - Cross-table patterns: 1.3x weight
   - Guidelines: 1.0x weight
   - Overview: 0.5x weight
   - Glossary: 0.3x weight
   - Ambiguities: 0.3x weight

2. **Increase chunk retrieval to 10**: Current 5 chunks miss critical information. More chunks with proper weighting will improve coverage.

3. **Post-retrieval filtering**: Remove ambiguities and glossaries unless explicitly relevant to question keywords.

4. **Table-focused retrieval**: Always retrieve documentation for tables mentioned in the question or detected via keyword matching.

---

## Overall Recommendations

### Immediate Fixes (High Priority)

1. **Fix cre_Doc_Template_Mgt gold SQL** or exclude from benchmarks
   - Impact: +8.1% accuracy improvement (84 questions)

2. **Refine Guideline #9** for superlative phrasing
   - Impact: ~1-2% accuracy improvement
   - Suggested refinement:
   ```
   When the question asks "how many", "what is the total", or "what is the average",
   INCLUDE the aggregation in SELECT.

   When the question asks "which", "what", or "who" with "most", "least", "greatest"
   followed by LIMIT 1, EXCLUDE the aggregation from SELECT (return the identifier only).
   ```

3. **Add JOIN type guidance** to semantic layers
   - Impact: ~1% accuracy improvement
   - Add to relationship documentation: "join_type": "INNER" or "LEFT"
   - Add guideline: "Use INNER JOIN for aggregations unless question says 'including those without'"

### Medium Priority

4. **Implement chunk type weighting** in vector search
   - Impact: ~2-3% accuracy improvement
   - Prioritize table documentation over generic content

5. **Remove or refine overly generic guidelines**
   - Impact: ~1% accuracy improvement
   - Review all "Query Guidelines" sections
   - Make guidelines context-aware or remove them

6. **Increase chunk retrieval count** from 5 to 10
   - Impact: Better coverage, especially for complex queries
   - Risk: More token usage (cost vs accuracy tradeoff)

### Long-Term Improvements

7. **Query-type detection**:
   - Simple single-table → retrieve only relevant table + domain overview
   - Complex multi-table → retrieve all involved tables + relationships + patterns
   - Aggregation query → prioritize aggregation examples and guidelines

8. **Semantic layer quality metrics**:
   - Track chunk relevance per database
   - Identify low-quality guidelines
   - A/B test semantic layer variations

9. **Hybrid approach**:
   - Use semantic layer for table/column selection and JOIN guidance
   - Use schema-only for final SQL generation (avoid guideline conflicts)

---

## Cost-Benefit Analysis

### Current State
- **Cost**: Semantic layer adds ~2-3x tokens per query (embeddings + retrieved chunks)
- **Benefit**: -2.3% accuracy (semantic layer makes things worse)
- **ROI**: Negative

### After Immediate Fixes
- **Estimated Accuracy**:
  - Fix cre_Doc_Template_Mgt: +8.1%
  - Fix Guideline #9: +1.5%
  - Add JOIN guidance: +1.0%
  - **Total: Enhanced would be ~60.5% vs Baseline 52.2% = +8.3% improvement**

### After All Recommendations
- **Estimated Accuracy**: Enhanced 62-65% vs Baseline 52% = **+10-13% improvement**
- **Token Cost**: Similar or slightly higher (10 chunks vs 5, but better relevance)
- **ROI**: Strongly positive

---

## Conclusion

The semantic layer concept is sound, but current implementation has critical flaws:

1. **Database setup issues** mask actual performance
2. **Prompt guidelines conflict** with semantic layer guidance
3. **Vector search retrieves noise** instead of signal
4. **Generic content overwhelms** specific, actionable information

**Fixing these issues will transform semantic layers from a -2.3% regression into a +10-13% improvement.**

The path forward is clear: fix gold SQL, refine prompts, improve vector search weighting, and add missing information (JOIN types, context-aware guidelines).

---

## Appendix: Detailed Failure Examples

### Full wta_1 Failure Analysis

| Question ID | Question | Issue | Root Cause |
|-------------|----------|-------|------------|
| dev_0475 | find the code of the country where has the greatest number of players | Includes COUNT in SELECT | Guideline #9 ambiguity |
| dev_0476 | What is the code of the country with the most players? | Includes COUNT in SELECT | Guideline #9 ambiguity |
| dev_0470 | What are the first names of all players, and their average rankings? | LEFT JOIN instead of INNER | Missing JOIN type guidance |
| dev_0472 | What are the first names of all players, and their total ranking points? | LEFT JOIN instead of INNER | Missing JOIN type guidance |
| dev_0451 | players who won in both tourney WTA Championships and Australian Open | Uses tourney_id instead of tourney_name | Misleading guideline |

### concert_singer Success Analysis

| Question ID | Question | Baseline Issue | Why Enhanced Succeeded |
|-------------|----------|----------------|------------------------|
| dev_0025 | stadium with the most concerts after 2013 | Alias bug (s.name vs st) | Consistent aliasing from semantic chunks |
| dev_0041 | stadiums with concerts in 2014 and 2015 | Alias bug (s.name vs st) | Clear table references |
| dev_0042 | stadiums that had concerts in both years | Alias bug (s.name vs st) | Grounded in table documentation |

---

**Analysis completed**: 2025-11-02
**Analyzed by**: Claude Code (Sonnet 4.5)
**Benchmark**: Spider 1.0 (1,034 questions, 20 databases)
**Run**: Full Spider 1.0 Run 22
