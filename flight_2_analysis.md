# flight_2 Regression Analysis

**Degradation:** 92.5% → 88.8% (-3.7%, -3 questions out of 80)

## Issue 1: Case Sensitivity + SELECT * (dev_0193)

**Question:** "Which airline has abbreviation 'UAL'?"

**Gold SQL:**
```sql
SELECT Airline FROM AIRLINES WHERE Abbreviation = "UAL"
```
Uses capitalized `Abbreviation` and selects specific column

**Run 12 SQL (✅):**
```sql
SELECT Airline FROM airlines WHERE Abbreviation = 'UAL'
```
Uses capitalized `Abbreviation`, selects specific column

**Run 13 SQL (❌):**
```sql
SELECT * FROM airlines WHERE abbreviation = 'UAL'
```
Uses lowercase `abbreviation` AND uses `SELECT *`

**Analysis:**

Two problems:
1. **Case sensitivity:** `abbreviation` (lowercase) vs `Abbreviation` (capitalized in schema)
2. **SELECT *:** Returns all columns instead of just the airline name

**Root Cause:**

The semantic layer (from Supabase) has lowercase column names:
```json
{
  "name": "abbreviation",  // lowercase from PostgreSQL
  "business_name": "Abbreviation"
}
```

But the actual Turso schema has capitalized columns.

Additionally, Phase 2 might have confused the LLM about which columns to select by providing too much context about all columns.

---

## Issue 2: Wrong JOIN Type (dev_0231)

**Question:** "Find the abbreviation and country of the airline that has fewest number of flights?"

**Gold SQL:**
```sql
SELECT T1.Abbreviation, T1.Country FROM AIRLINES AS T1
JOIN FLIGHTS AS T2 ON T1.uid = T2.Airline
GROUP BY T1.Airline
ORDER BY count(*) LIMIT 1
```
Uses INNER JOIN (only airlines with flights)

**Run 12 SQL (✅):**
```sql
SELECT airlines.abbreviation, airlines.country
FROM airlines
JOIN flights ON airlines.uid = flights.airline
GROUP BY airlines.uid
ORDER BY COUNT(flights.flightno) ASC
LIMIT 1;
```
Uses INNER JOIN correctly

**Run 13 SQL (❌):**
```sql
SELECT airlines.abbreviation, airlines.country
FROM airlines
LEFT JOIN flights ON airlines.uid = flights.airline
GROUP BY airlines.uid
ORDER BY COUNT(flights.flightno) ASC
LIMIT 1;
```
Uses LEFT JOIN (includes airlines with 0 flights!)

**Analysis:**

The question asks for "the airline that has fewest number of flights", which implicitly means:
- Among airlines that HAVE flights, which has the fewest?

Using LEFT JOIN would include airlines with 0 flights, making them have the "fewest" (zero).

**Root Cause:**

Phase 2 might have over-emphasized the relationship guidance, leading the LLM to be "overly inclusive" by using LEFT JOIN to ensure all airlines are considered.

Looking at common_mistakes in the semantic layer might reveal guidance like:
- "DO NOT exclude airlines without flights"
- Or similar guidance that led to LEFT JOIN

This is a subtle semantic issue where the LLM interpreted "fewest flights" to potentially include zero flights.

---

## Issue 3: Logic Error in Aggregation (dev_0222)

**Question:** "Which city has the most frequent destination airport?"

**Gold SQL:**
```sql
SELECT T1.City FROM AIRPORTS AS T1
JOIN FLIGHTS AS T2 ON T1.AirportCode = T2.DestAirport
GROUP BY T1.City
ORDER BY count(*) DESC LIMIT 1
```
Joins airports.AirportCode to flights.DestAirport, groups by City

**Run 12 SQL (❓ How did this pass?):**
```sql
SELECT SourceAirport FROM flights
GROUP BY SourceAirport
ORDER BY COUNT(DestAirport) DESC LIMIT 1
```
Returns SourceAirport, not City, and doesn't join with airports

**Run 13 SQL (❌):**
```sql
SELECT City FROM airports
GROUP BY City
ORDER BY COUNT(DestAirport) DESC LIMIT 1
```
Groups by City but doesn't COUNT from flights table!

**Analysis:**

Run 13 has a fundamental logic error:
- It tries to count `DestAirport` column from airports table
- But `DestAirport` is in the flights table, not airports
- The query should join flights to count how many times each city appears as a destination

**Root Cause:**

The semantic layer might have unclear guidance about:
- When to join tables for aggregation
- How to count occurrences from related tables

The LLM tried to shortcut the query by grouping airports.City without realizing it needs to count from flights table.

---

## Summary of Issues

### 1. **Case Sensitivity (2 out of 3 failures)**
- Semantic layer: lowercase column names (`abbreviation`)
- Turso schema: capitalized column names (`Abbreviation`)
- **Same root cause as network_1**

### 2. **SELECT * Instead of Specific Columns (1 failure)**
- Phase 2 might have provided too much column context
- LLM used `SELECT *` instead of selecting specific columns
- **Fix:** Add guidance to always select specific columns mentioned in question

### 3. **Wrong JOIN Type (1 failure)**
- Used LEFT JOIN when INNER JOIN was appropriate
- Misinterpreted "fewest flights" to include zero flights
- **Fix:** Clarify when to use INNER vs LEFT JOIN

### 4. **Missing JOIN in Aggregation (1 failure)**
- Tried to COUNT column from wrong table
- Didn't join to the table containing the data to count
- **Fix:** Add clear guidance about joining for aggregation

## Recommendations

### Priority 1: Fix Case Sensitivity (Critical)
Same as network_1 - generate semantic layers from Turso, not Supabase.

### Priority 2: Add SELECT Best Practice
Add to query guidelines:
```
"Always SELECT only the specific columns mentioned in the question.
Avoid SELECT * unless explicitly asked for all columns."
```

### Priority 3: Clarify JOIN Types
Add guidance:
```
"Use INNER JOIN when the question implies 'among entities that have a relationship'.
Example: 'airline with fewest flights' means airlines that HAVE flights (INNER JOIN).

Use LEFT JOIN when explicitly asked to include entities without relationships.
Example: 'all airlines and their flight counts, including those with no flights'."
```

### Priority 4: Aggregation Join Guidance
Add to common_query_patterns:
```json
{
  "question": "Which city has the most flights?",
  "explanation": "Join airports to flights, then group by city and count from flights table.",
  "sql": "SELECT a.city FROM airports a JOIN flights f ON a.airportcode = f.destairport GROUP BY a.city ORDER BY COUNT(*) DESC LIMIT 1",
  "common_mistakes": ["Grouping by city without counting from flights table"]
}
```

## Pattern Across All Three Degraded Databases

| Issue | student_transcripts | network_1 | flight_2 |
|-------|---------------------|-----------|----------|
| **Case sensitivity** | No | Yes (2/3) | Yes (1/3) |
| **Wrong column selection** | Yes (ID vs name) | No | Yes (SELECT *) |
| **Wrong JOIN logic** | Yes (INTERSECT) | Yes (wrong FK) | Yes (LEFT vs INNER) |
| **Missing aggregation** | Yes (missing COUNT) | No | Yes (COUNT wrong table) |
| **Ambiguous synonyms** | Yes ("Degree ID") | No | No |

**Common root causes:**
1. **Case sensitivity** - affects network_1, flight_2 (and likely others)
2. **Phase 2 guidance being too helpful** - provides context that confuses rather than clarifies
3. **Need for query pattern examples** - LLM needs more concrete examples of correct patterns
