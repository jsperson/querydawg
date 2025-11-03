# Turso Setup Guide for QueryDawg

**Date**: 2025-11-03
**Purpose**: Step-by-step guide to integrate hosted Turso for Spider benchmark databases

---

## Prerequisites

- [ ] Turso account (free tier)
- [ ] Turso CLI installed
- [ ] Spider SQLite databases in `data/spider/database/`

---

## Step 1: Install Turso CLI

```bash
# Install Turso CLI
curl -sSfL https://get.tur.so/install.sh | bash

# Add to PATH if needed
export PATH="$HOME/.turso:$PATH"

# Verify installation
turso --version
```

---

## Step 2: Create Turso Account & Login

```bash
# Login (opens browser for authentication)
turso auth login

# Verify login
turso auth whoami
```

---

## Step 3: Create Organization (Optional)

```bash
# Create organization for better organization
turso org create querydawg

# Or use default personal organization
```

---

## Step 4: Upload Spider Databases

### Manual Upload (One at a time)

```bash
# Upload a single database
turso db create concert_singer \
  --from-file data/spider/database/concert_singer/concert_singer.sqlite

# Verify
turso db show concert_singer
```

### Automated Upload (All databases)

Use the provided script:

```bash
# Upload all Spider databases
python scripts/upload_to_turso.py

# This will:
# 1. Find all .sqlite files in data/spider/database/
# 2. Create Turso databases for each
# 3. Upload the SQLite files
# 4. Generate a token mapping file
```

---

## Step 5: Get Database URLs and Tokens

### Individual Database

```bash
# Get database URL
turso db show concert_singer --url
# Output: libsql://concert_singer-<org>.turso.io

# Create auth token
turso db tokens create concert_singer
# Output: eyJhbGc... (save this!)
```

### All Databases (Automated)

```bash
# Generate tokens for all databases
python scripts/generate_turso_tokens.py

# This creates: .env.turso with all tokens
```

---

## Step 6: Configure Environment Variables

### Local Development

Add to `.env`:

```bash
# Turso configuration
TURSO_ORG=querydawg
TURSO_BASE_URL=https://querydawg.turso.io

# Option 1: Single shared token (easiest)
TURSO_TOKEN=<your-org-level-token>

# Option 2: Per-database tokens (more secure)
TURSO_TOKEN_CONCERT_SINGER=<token>
TURSO_TOKEN_WTA_1=<token>
# ... etc
```

### Railway Deployment

```bash
# Set in Railway dashboard or via CLI
railway variables set TURSO_ORG=querydawg
railway variables set TURSO_BASE_URL=https://querydawg.turso.io
railway variables set TURSO_TOKEN=<your-token>
```

---

## Step 7: Test Connection

```bash
# Test Turso connection
python scripts/test_turso_connection.py

# Expected output:
# ✓ Connected to Turso
# ✓ Databases found: 20
# ✓ Test query successful
```

---

## Step 8: Migrate Schema Extraction

```bash
# Test schema extraction from Turso
python scripts/test_turso_schema.py concert_singer

# Expected output:
# ✓ Schema extracted
# ✓ Tables: 4
# ✓ Foreign keys: 2
```

---

## Step 9: Regenerate Semantic Layers

```bash
# Regenerate semantic layers using Turso as source
python scripts/regenerate_all_semantic_layers.py --source turso

# This will:
# 1. Extract schema from Turso (SQLite)
# 2. Sample data from Turso
# 3. Generate semantic layers
# 4. Store in Supabase (metadata)
```

---

## Step 10: Update Benchmark Runner

The benchmark runner will automatically use Turso for query execution:

```bash
# Run benchmark (executes against Turso)
# Via Vercel UI or:
python scripts/run_benchmark.py --limit 10
```

---

## Verification Checklist

- [ ] Turso CLI installed and authenticated
- [ ] All 20 Spider databases uploaded to Turso
- [ ] Environment variables configured
- [ ] Test connection successful
- [ ] Schema extraction working
- [ ] Semantic layers regenerated from Turso
- [ ] Benchmark runs against Turso
- [ ] Results stored in Supabase

---

## Database URLs

After upload, your databases will be accessible at:

```
libsql://concert_singer-querydawg.turso.io
libsql://wta_1-querydawg.turso.io
libsql://battle_death-querydawg.turso.io
... (20 total)
```

---

## Turso CLI Quick Reference

```bash
# List all databases
turso db list

# Show database info
turso db show <db-name>

# Get database URL
turso db show <db-name> --url

# Create auth token
turso db tokens create <db-name>

# Delete database (if needed)
turso db destroy <db-name>

# Shell into database
turso db shell <db-name>

# Execute query
turso db shell <db-name> "SELECT COUNT(*) FROM concerts"
```

---

## Troubleshooting

### Issue: "Database already exists"

```bash
# Delete and recreate
turso db destroy concert_singer
turso db create concert_singer --from-file concert_singer.sqlite
```

### Issue: "Authentication failed"

```bash
# Re-login
turso auth logout
turso auth login
```

### Issue: "Token expired"

```bash
# Generate new token
turso db tokens create <db-name>
```

### Issue: "Can't find SQLite file"

```bash
# Verify file exists
ls data/spider/database/concert_singer/concert_singer.sqlite

# Check file permissions
chmod 644 data/spider/database/*/*.sqlite
```

---

## Cost Monitoring

Turso free tier limits:
- 500 databases ✅ (we have 20)
- 9 GB storage ✅ (we use ~100 MB)
- 1 billion row reads/month ✅ (we use ~10M)

Check usage:

```bash
turso org show
# Shows: storage used, databases, monthly reads
```

---

## Next Steps

After successful Turso integration:

1. Run benchmark to compare SQLite vs PostgreSQL results
2. Verify 0 gold SQL failures (vs 84 with Supabase)
3. Measure query performance improvement
4. Update documentation

---

## Rollback Plan

If issues arise:

1. Keep Supabase running (metadata is still there)
2. Temporarily switch back to Supabase for queries
3. Debug Turso integration offline
4. Re-migrate when ready

The hybrid architecture allows gradual migration with zero downtime.
