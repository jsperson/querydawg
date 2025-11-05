# network_1 Regression Analysis

**Degradation:** 87.5% → 82.1% (-5.4%, -3 questions out of 56)

## Issue 1: Case Sensitivity (Confirmed)

**Semantic layer (from Supabase/PostgreSQL):** `friend`, `highschooler`, `likes` (lowercase)
**Actual Turso schema (from Spider SQLite):** `Friend`, `Highschooler`, `Likes` (capitalized)

### Evidence from dev_0904:

**Run 12 SQL (✅):**
```sql
SELECT h.name, COUNT(l.liked_id) AS number_of_likes
FROM Highschooler h
JOIN Likes l ON h.ID = l.student_id
GROUP BY h.ID;
```
Uses capitalized `Highschooler`, `Likes`

**Run 13 SQL (❌):**
```sql
SELECT highschooler.name, COUNT(likes.liked_id) AS number_of_likes
FROM highschooler
JOIN likes ON highschooler.ID = likes.student_id
GROUP BY highschooler.name;
```
Uses lowercase `highschooler`, `likes`

**Root Cause:**
- Semantic layers are generated from Supabase (PostgreSQL)
- PostgreSQL automatically lowercases unquoted identifiers
- Original Spider databases in Turso have capitalized table names
- SQLite is case-sensitive for table names

---

## Issue 2: Logic Errors from Phase 2 Guidance

### Error 1: Wrong JOIN Column (dev_0893)

**Question:** "Count the number of friends Kyle has."

**Gold SQL:**
```sql
SELECT count(*) FROM Friend AS T1
JOIN Highschooler AS T2 ON T1.student_id = T2.id
WHERE T2.name = "Kyle"
```
Joins on `student_id` (the person WHO HAS the friend)

**Run 12 SQL (✅):**
```sql
SELECT COUNT(friend_id) FROM Friend
WHERE student_id = (SELECT ID FROM Highschooler WHERE name = 'Kyle')
```
Correctly filters by `student_id`

**Run 13 SQL (❌):**
```sql
SELECT COUNT(*) FROM Friend
JOIN Highschooler ON Friend.friend_id = Highschooler.ID
WHERE Highschooler.name = 'Kyle'
```
Incorrectly joins on `friend_id` (the person WHO IS the friend)

**Analysis:**

Looking at the network_1 semantic layer's bridge table guidance:

```json
{
  "table": "friend",
  "relationships": [
    {
      "column": "student_id",
      "is_bridge_table": true,
      "business_meaning": "Links a student to their friends.",
      "complete_join_path": ["friend → highschooler"]
    },
    {
      "column": "friend_id",
      "is_bridge_table": true,
      "business_meaning": "Links a friend to the student they are friends with.",
      "complete_join_path": ["friend → highschooler"]
    }
  ]
}
```

**The Problem:**
Both columns have the SAME join path `friend → highschooler`, which doesn't clarify WHICH column to use for WHICH direction of the relationship.

The LLM chose the wrong column (`friend_id` instead of `student_id`) for finding Kyle's friends.

---

### Error 2: Wrong GROUP BY Column (dev_0904)

**Question:** "Show the names of high schoolers who have likes, and numbers of likes for each."

**Gold SQL:**
```sql
SELECT T2.name, count(*) FROM Likes AS T1
JOIN Highschooler AS T2 ON T1.student_id = T2.id
GROUP BY T1.student_id
```
Groups by `student_id` (unique identifier)

**Run 12 SQL (✅):**
```sql
SELECT h.name, COUNT(l.liked_id) AS number_of_likes
FROM Highschooler h
JOIN Likes l ON h.ID = l.student_id
GROUP BY h.ID;
```
Groups by `h.ID` (correct)

**Run 13 SQL (❌):**
```sql
SELECT highschooler.name, COUNT(likes.liked_id) AS number_of_likes
FROM highschooler
JOIN likes ON highschooler.ID = likes.student_id
GROUP BY highschooler.name;
```
Groups by `highschooler.name` (wrong - names aren't unique!)

**Analysis:**

This is a subtle error. The question asks for "names" and "numbers of likes for each", which could mean:
- For each STUDENT (correct - group by ID)
- For each NAME (incorrect - what if two students have the same name?)

Phase 2 semantic guidance might have over-emphasized natural language, causing the LLM to literally group by `name` instead of the proper practice of grouping by ID and selecting name.

---

### Error 3: Wrong JOIN Logic (dev_0906)

**Question:** "What is the name of the high schooler who has the greatest number of likes?"

**Gold SQL:**
```sql
SELECT T2.name FROM Likes AS T1
JOIN Highschooler AS T2 ON T1.student_id = T2.id
GROUP BY T1.student_id
ORDER BY count(*) DESC LIMIT 1
```
Joins on `student_id` → finds who GIVES likes

**Run 12 SQL (✅):**
```sql
SELECT h.name FROM Highschooler h
JOIN Likes l ON h.ID = l.student_id
GROUP BY h.ID
ORDER BY COUNT(l.liked_id) DESC LIMIT 1
```
Correctly joins on `l.student_id`

**Run 13 SQL (❌):**
```sql
SELECT highschooler.name FROM likes
JOIN highschooler ON likes.liked_id = highschooler.ID
GROUP BY highschooler.ID
ORDER BY COUNT(likes.student_id) DESC LIMIT 1
```
Incorrectly joins on `liked_id` → finds who RECEIVES likes

**Analysis:**

The question is ambiguous:
- "who has the greatest number of likes" could mean:
  - Who GIVES the most likes? (correct interpretation)
  - Who RECEIVES the most likes? (Run 13's interpretation)

Looking at the semantic layer for the `likes` table:

```json
{
  "columns": [
    {
      "name": "student_id",
      "business_meaning": "The unique identifier for a student who likes another student.",
      "disambiguation": {
        "usage_guidance": "Use likes.student_id to find who a student likes; use friend.student_id for friendships."
      }
    },
    {
      "name": "liked_id",
      "business_meaning": "The unique identifier for a student who is liked by another student.",
      "disambiguation": {
        "usage_guidance": "Use likes.liked_id to identify the student who is liked."
      }
    }
  ]
}
```

The disambiguation says:
- `student_id`: "find who a student likes" (who GIVES likes)
- `liked_id`: "identify the student who is liked" (who RECEIVES likes)

**The Problem:**
The phrase "has the greatest number of likes" is ambiguous in English, and the LLM interpreted it as "who is liked the most" (passive voice) rather than "who gives the most likes" (active voice).

The gold SQL interpretation uses `student_id`, suggesting "has likes" means "possesses/gives likes", not "receives likes".

---

## Summary of Issues

### 1. **Case Sensitivity (2 out of 3 failures)**
- Semantic layer: lowercase `friend`, `highschooler`, `likes`
- Turso schema: capitalized `Friend`, `Highschooler`, `Likes`
- SQLite is case-sensitive
- **Fix:** Generate semantic layers from Turso OR normalize Turso to lowercase

### 2. **Ambiguous Bridge Table Guidance (1 failure)**
- Both `student_id` and `friend_id` have same join path
- Doesn't clarify which column for which direction
- **Fix:** Make join paths directional with role clarity

### 3. **Over-Literal Natural Language Mapping (1 failure)**
- Grouped by `name` instead of `ID` because question asks for "names"
- **Fix:** Add guidance to always group by IDs, not display columns

### 4. **Ambiguous Question Interpretation (1 failure)**
- "has likes" interpreted as passive (receives) vs active (gives)
- **Fix:** Requires better context understanding or examples

## Recommendations

### Priority 1: Fix Case Sensitivity
Query Turso API to get actual schema and generate semantic layers from Turso, not Supabase.

### Priority 2: Improve Bridge Table Guidance
Instead of:
```json
{
  "column": "student_id",
  "complete_join_path": ["friend → highschooler"]
}
```

Use:
```json
{
  "column": "student_id",
  "complete_join_path": ["friend → highschooler"],
  "join_semantics": "To find all friends OF a student (student_id = <student's ID>), join friend.friend_id to highschooler.id"
}
```

### Priority 3: Add GROUP BY Best Practices
Add to query guidelines:
```
"When aggregating, always GROUP BY unique identifiers (IDs), not display names or descriptions."
```

### Priority 4: Add Disambiguation Examples
For ambiguous cases like "has likes", add example queries:
```json
{
  "question": "Who has the most likes?",
  "clarification": "This means who GIVES the most likes, not who RECEIVES them.",
  "sql": "SELECT h.name FROM Likes l JOIN Highschooler h ON l.student_id = h.id GROUP BY l.student_id ORDER BY COUNT(*) DESC LIMIT 1"
}
```
