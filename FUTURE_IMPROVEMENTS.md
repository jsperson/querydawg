# Future Improvements

## High Priority

### 1. Move Database Connection Configuration to Frontend UI
**Current State:**
- Database connections (`DATABASE_URL`, `SUPABASE_URL`, etc.) are hard-coded in environment variables
- Requires redeployment to change connections
- Limited to single database/project configuration

**Proposed Improvement:**
- Add a configuration page in the admin interface
- Allow users to configure multiple database connections via UI
- Store connection strings securely (encrypted) in the metadata store
- Support multiple projects/databases per deployment
- Add connection testing functionality

**Benefits:**
- No redeployment needed to change databases
- Multi-tenant support (multiple users/projects)
- Easier for non-technical users to configure
- Can support demo/trial databases easily

**Implementation Notes:**
- Encrypt connection strings before storing
- Add UI in `/admin/settings` or `/admin/connections`
- Use connection pooling for efficiency
- Validate connections before saving
- Consider using connection presets (Supabase, PostgreSQL, etc.)

---

## Medium Priority

### 2. wta_1 Database Optimization
- Current: 510k rows in rankings table
- Consider: Pagination, indexing, or sampling for better performance

### 3. Error Handling Improvements
- Add user-friendly error messages
- Implement retry logic for transient failures
- Better logging for debugging

---

## MCP Server Integration Opportunities

### 4. Postgres MCP - Automated Benchmark Analysis & Research Insights
**Current State:**
- 20+ benchmark runs stored in Supabase
- Manual analysis required to extract research insights
- SQL queries written ad-hoc for data exploration

**Proposed Improvements:**
- **Automated Analysis Scripts:**
  - Compare baseline vs enhanced accuracy across databases
  - Statistical significance testing for research validation
  - Cost-effectiveness analysis (accuracy improvement per dollar spent)
  - Identify which database types benefit most from semantic layers
  - Track performance trends across benchmark runs over time

- **Research Report Generation:**
  - Auto-generate tables/charts for thesis documentation
  - Export benchmark summaries in research-ready formats
  - Analyze failure patterns to improve semantic layer prompts
  - Query-based insights (e.g., "Which questions improved most with enhanced?")

- **Example Analysis Queries:**
  - Overall baseline vs enhanced comparison with statistical tests
  - Performance breakdown by database domain
  - Cost analysis per question difficulty level
  - Retry pattern analysis for reliability metrics
  - Semantic layer effectiveness by database characteristics

**Benefits:**
- Accelerate research data analysis
- Generate publication-ready statistics
- Identify optimization opportunities for semantic layers
- Support hypothesis validation with quantitative data

### 5. Context7 MCP - Development Documentation Access
**Use Cases:**
- Fetch latest Pinecone best practices for vector search optimization
- Get up-to-date FastAPI/Next.js patterns when adding features
- Access Supabase query optimization techniques
- Reference current library versions during development

**Benefits:**
- Faster feature development with current best practices
- Avoid deprecated patterns
- Optimize performance using latest recommendations

### 6. Railway MCP - Deployment Operations & Monitoring
**Use Cases:**
- Pull deployment/build logs when debugging production issues
- Programmatically manage environment variables
- Check deployment status without dashboard access
- Automated log monitoring for error detection

**Benefits:**
- Faster debugging of production issues
- Scriptable deployment operations
- Proactive error detection

---

_Last Updated: 2025-10-31_
