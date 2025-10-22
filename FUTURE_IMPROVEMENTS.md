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

_Last Updated: 2025-10-22_
