# student_transcripts_tracking Regression Analysis

**Degradation:** 79.5% → 74.4% (-5.1%, -4 questions out of 78)

## Root Cause: Ambiguous Synonyms Leading to Wrong Column Selection

### Failed Question 1: "How many different degrees are offered?"

**Run 12 SQL (✅ Correct):**
```sql
SELECT COUNT(DISTINCT degree_summary_name) FROM Degree_Programs;
```

**Run 13 SQL (❌ Incorrect):**
```sql
SELECT COUNT(DISTINCT degree_program_id) FROM Degree_Programs;
```

**Analysis:**

Looking at the degree_programs table in the semantic layer:

**degree_program_id:**
- Synonyms: "Program ID", **"Degree ID"**, "Program Key"
- Business meaning: "Unique identifier for each degree program."

**degree_summary_name:**
- Synonyms: "Program Name", **"Degree Title"**, "Program Title"
- Business meaning: "The name or title of the degree program."

**The Problem:**
The semantic layer added **"Degree ID"** as a synonym for `degree_program_id`. When the question asks "how many different degrees," the LLM may have matched:
- "degrees" → "Degree ID" (synonym) → `degree_program_id`

But the correct interpretation should be:
- "degrees" → "Degree Title" (synonym) → `degree_summary_name`

**Why Run 12 Worked:**
Without the synonym guidance, the LLM likely used common sense or schema inspection to realize that counting degree names makes more sense than counting IDs.

**Why Run 13 Failed:**
The Phase 2 synonym "Degree ID" explicitly linked "degree" to the ID column, causing the LLM to use the wrong column.

---

### Failed Question 2: "What is the maximum number of times that a course shows up in different transcripts and what is that course's enrollment id?"

**Run 12 SQL (✅ Correct):**
```sql
SELECT student_course_id, COUNT(*) as course_count
FROM transcript_contents
GROUP BY student_course_id
ORDER BY course_count DESC
LIMIT 1;
```
Returns BOTH the ID and the count.

**Run 13 SQL (❌ Incorrect):**
```sql
SELECT student_course_id
FROM transcript_contents
GROUP BY student_course_id
ORDER BY COUNT(*) DESC
LIMIT 1;
```
Returns ONLY the ID, missing the count.

**Analysis:**

The question explicitly asks for TWO things:
1. "maximum number of times" → need COUNT(*)
2. "course's enrollment id" → need student_course_id

Run 12 correctly returns both.
Run 13 returns only the ID.

**Possible causes:**
- Phase 2 disambiguation for `student_course_id` might have confused the LLM
- The semantic guidance might have over-emphasized the ID column
- The LLM might have been distracted by Phase 2 context

Looking at the semantic layer for student_course_id in transcript_contents:

```json
{
  "name": "student_course_id",
  "disambiguation": {
    "usage_guidance": "Use this ID to reference specific course enrollments in transcripts.",
    "appears_in_tables": ["student_enrolment_courses"],
    "this_table_meaning": "References a student's course enrollment in the transcript_contents table.",
    "other_table_meanings": {
      "student_enrolment_courses": "Unique identifier for a student's course enrollment."
    }
  }
}
```

**The Problem:**
The disambiguation emphasizes "reference specific course enrollments" which might have led the LLM to think it only needs to return the ID for reference, not realize it also needs to COUNT.

---

### Failed Question 3: "Find the semester when both Master students and Bachelor students got enrolled in."

**Run 12 SQL (✅ Correct):**
```sql
SELECT DISTINCT semester_id
FROM Student_Enrolment
WHERE degree_program_id IN (
  SELECT degree_program_id FROM Degree_Programs WHERE degree_summary_name LIKE '%Master%'
)
INTERSECT
SELECT DISTINCT semester_id
FROM Student_Enrolment
WHERE degree_program_id IN (
  SELECT degree_program_id FROM Degree_Programs WHERE degree_summary_name LIKE '%Bachelor%'
);
```
Uses INTERSECT to find semesters where BOTH degree types enrolled.

**Run 13 SQL (❌ Incorrect):**
```sql
SELECT DISTINCT semesters.semester_name
FROM student_enrolment
JOIN students ON student_enrolment.student_id = students.student_id
JOIN semesters ON student_enrolment.semester_id = semesters.semester_id
WHERE students.student_id IN (
  SELECT student_id FROM student_enrolment
  WHERE degree_program_id IN (SELECT degree_program_id FROM degree_programs WHERE degree_summary_name LIKE '%Master%')
)
AND students.student_id IN (
  SELECT student_id FROM student_enrolment
  WHERE degree_program_id IN (SELECT degree_program_id FROM degree_programs WHERE degree_summary_name LIKE '%Bachelor%')
);
```
Incorrectly looks for STUDENTS enrolled in both programs, not SEMESTERS.

**Analysis:**

The question asks: "semester when both Master students and Bachelor students got enrolled"

**Correct interpretation:** Find semesters where at least one Master student AND at least one Bachelor student enrolled.

**Run 13's incorrect interpretation:** Find students who are enrolled in BOTH Master AND Bachelor programs simultaneously.

**The Problem:**

Phase 2 guidance likely emphasized the JOIN path through students:
- student_enrolment → students
- student_enrolment → degree_programs
- student_enrolment → semesters

The semantic layer has this guidance:
```json
{
  "question": "What is the enrollment history of a student?",
  "explanation": "Join student_enrolment with students and filter by student_id.",
  "involves_joins": ["students"]
}
```

This pattern might have led the LLM to think the question is about STUDENTS rather than SEMESTERS.

---

## Summary of Issues

### 1. **Overly Specific Synonyms**
- "Degree ID" as synonym for `degree_program_id` caused wrong column selection
- Synonyms should be carefully chosen to avoid ambiguity

### 2. **Incomplete Query Generation**
- Phase 2 guidance may have over-emphasized ID columns
- LLM forgot to include COUNT(*) in SELECT clause

### 3. **Incorrect Join Strategy**
- Phase 2 join path recommendations led to wrong table focus
- Question was about semesters, but LLM focused on students

## Recommendations

### Fix 1: Refine Synonyms
**Bad synonym:**
```json
"degree_program_id": {
  "synonyms": ["Program ID", "Degree ID", "Program Key"]
}
```

**Better synonym:**
```json
"degree_program_id": {
  "synonyms": ["Program ID", "Program Key", "Degree Program Identifier"]
}
```
Remove "Degree ID" which is too close to "degree" in natural language.

### Fix 2: Clarify Usage Guidance
**Current:**
```json
"usage_guidance": "Use this ID to reference specific course enrollments in transcripts."
```

**Better:**
```json
"usage_guidance": "Use this ID to reference specific course enrollments. When counting occurrences, include both the ID and COUNT(*) in SELECT."
```

### Fix 3: Add Intent-Based Query Patterns
**Current:**
```json
{
  "question": "What is the enrollment history of a student?",
  "explanation": "Join student_enrolment with students and filter by student_id."
}
```

**Add:**
```json
{
  "question": "Which semesters had both Master and Bachelor students?",
  "explanation": "Use INTERSECT on semester_id from student_enrolment filtered by degree program type.",
  "involves_joins": ["degree_programs"]
}
```

## Next Steps

1. Review all synonyms in semantic layers for potential ambiguity
2. Test synonym changes on student_transcripts_tracking
3. Add more specific query pattern examples for complex questions
4. Consider reducing synonym count to only truly unambiguous alternatives
