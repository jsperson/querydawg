# QueryDawg Services Configuration
**Last Updated:** 2025-10-16

This document tracks all external services, accounts, and configurations for the QueryDawg project.

---

## Service Accounts

### ✅ Railway (Backend Hosting)
- **Account:** Created
- **Project:** querydawg-backend
- **URL:** [To be added after deployment]
- **Status:** Connected to GitHub repository
- **Configuration:** `railway.toml` in repo root
- **Cost:** Free $5/month credit → ~$10-15/month estimated

---

### ✅ Vercel (Frontend Hosting)
- **Account:** Created
- **Project:** [To be added]
- **URL:** [To be added after deployment]
- **Status:** Account setup complete
- **Configuration:** Will auto-detect Next.js from `frontend/` directory
- **Cost:** Free tier

---

### ✅ Supabase (PostgreSQL Database)
- **Account:** Created
- **Project Name:** querydawg
- **Project ID:** invnoyuelwobmstjhidr
- **Project URL:** https://invnoyuelwobmstjhidr.supabase.co
- **Database Host:** db.invnoyuelwobmstjhidr.supabase.co
- **Region:** [Add your selected region]
- **Status:** Active
- **Cost:** Free tier (500MB storage, 2GB bandwidth)

**API Endpoints:**
- REST API: `https://invnoyuelwobmstjhidr.supabase.co/rest/v1`
- Auth: `https://invnoyuelwobmstjhidr.supabase.co/auth/v1`
- Storage: `https://invnoyuelwobmstjhidr.supabase.co/storage/v1`
- Realtime: `wss://invnoyuelwobmstjhidr.supabase.co/realtime/v1`

**Connection Details:**
- Database connection string: `postgresql://postgres:[PASSWORD]@db.invnoyuelwobmstjhidr.supabase.co:5432/postgres`
- API Keys: See Supabase Dashboard > Settings > API
  - `anon` key (public)
  - `service_role` key (secret, for backend only)

---

### ✅ Pinecone (Vector Database)
- **Account:** Created
- **Index Name:** querydawg-semantic
- **Environment:** aped-4627-b74a
- **Dimensions:** 1536 (for OpenAI text-embedding-3-small)
- **Metric:** cosine
- **Vector Type:** dense
- **Host:** https://querydawg-semantic-01blwrk.svc.aped-4627-b74a.pinecone.io
- **Status:** Active
- **Cost:** Free tier (100K vectors, 1 index)

**API Configuration:**
- API Key: See Pinecone Console > API Keys
- Region: Auto-assigned (aped-4627-b74a)

---

### ⏳ OpenAI (LLM & Embeddings)
- **Account:** [To be verified]
- **API Key:** [To be created]
- **Status:** Pending setup
- **Cost:** ~$100-180 for entire project

**Models to Use:**
- `gpt-4o-mini` - Primary text-to-SQL model ($0.15/$0.60 per 1M tokens)
- `gpt-4o` - Comparison/evaluation ($2.50/$10.00 per 1M tokens)
- `text-embedding-3-small` - Vector embeddings ($0.02 per 1M tokens)

**Safety Settings:**
- Set spending limit: $50/month hard limit
- Email alerts at: $10, $25, $40

---

## Environment Variables Summary

All environment variables are documented in `.env.example`. To set up:

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

**Required Variables:**
- `OPENAI_API_KEY` - From OpenAI platform
- `PINECONE_API_KEY` - From Pinecone console
- `SUPABASE_URL` - https://invnoyuelwobmstjhidr.supabase.co
- `SUPABASE_ANON_KEY` - From Supabase dashboard
- `SUPABASE_SERVICE_ROLE_KEY` - From Supabase dashboard
- `DATABASE_URL` - PostgreSQL connection string
- `NEXT_PUBLIC_API_URL` - Backend API URL (Railway after deployment)

---

## Network Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VERCEL (Frontend)                    │
│         https://[project].vercel.app                    │
│               Next.js 14 + TypeScript                   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS REST API
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  RAILWAY (Backend)                      │
│          https://[project].railway.app                  │
│                  FastAPI (Python)                       │
└───┬──────────────┬──────────────┬──────────────┬────────┘
    │              │              │              │
    ↓              ↓              ↓              ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ OpenAI   │  │Pinecone  │  │Supabase  │  │Supabase  │
│   API    │  │ Vectors  │  │PostgreSQL│  │ Storage  │
│platform. │  │aped-4627 │  │invnoyuel │  │invnoyuel │
│openai.com│  │-b74a     │  │wobmstjhi │  │wobmstjhi │
│          │  │          │  │dr        │  │dr        │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

---

## Database Schemas

### Supabase PostgreSQL Structure

**Planned Schemas:**
```
postgres/
├── public/                    # Default schema
│   └── databases              # Catalog of Spider databases
├── spider/                    # Spider dataset schemas
│   ├── concert_singer/        # Each database as separate schema
│   ├── pets_1/
│   ├── flight_2/
│   └── ...
├── semantic_layer/            # Semantic documentation
│   └── documents              # Natural language docs
└── evaluation/                # Evaluation results
    ├── runs
    └── results
```

---

## Security Notes

### Secrets Management
- ✅ `.env` is in `.gitignore` - NEVER commit
- ✅ `.env.example` is in git - safe (no real keys)
- ✅ Use environment variables in Railway/Vercel dashboards for production
- ✅ Rotate API keys if accidentally committed

### API Key Security
- **Supabase `anon` key:** Can be exposed in frontend (has RLS protection)
- **Supabase `service_role` key:** NEVER expose to frontend, backend only
- **OpenAI API key:** Backend only, NEVER expose to frontend
- **Pinecone API key:** Backend only, NEVER expose to frontend

### Database Access
- Supabase has Row Level Security (RLS) enabled by default
- Use `service_role` key only in backend for full access
- Frontend uses `anon` key with RLS policies

---

## Cost Tracking

| Service | Plan | Monthly Cost | Status |
|---------|------|--------------|--------|
| Railway | Hobby | $10-15 | Active |
| Vercel | Free | $0 | Active |
| Supabase | Free | $0 | Active |
| Pinecone | Free | $0 | Active |
| OpenAI | Pay-as-you-go | ~$100-180 (project total) | Pending |
| **Total** | | **~$110-195 (project)** | |

---

## Service Dashboards

Quick links for managing services:

- **Railway:** https://railway.app/dashboard
- **Vercel:** https://vercel.com/dashboard
- **Supabase:** https://supabase.com/dashboard/project/invnoyuelwobmstjhidr
- **Pinecone:** https://app.pinecone.io
- **OpenAI:** https://platform.openai.com/account

---

## Troubleshooting

### Common Issues

**Supabase Connection Issues:**
- Check if database is paused (free tier pauses after 7 days inactivity)
- Verify password is correct in connection string
- Check network connectivity

**Pinecone Connection Issues:**
- Verify API key is correct
- Check index name matches: `querydawg-semantic`
- Ensure host URL is correct

**OpenAI Rate Limits:**
- Monitor usage at https://platform.openai.com/usage
- Increase spending limits if needed
- Use exponential backoff for retries

---

## Next Steps

- [ ] Complete OpenAI account setup
- [ ] Get all API keys and update `.env`
- [ ] Test connections to all services
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
- [ ] Load Spider databases into Supabase

---

**Notes:**
- Keep this document updated as services are deployed
- Add production URLs once deployed
- Document any service configuration changes
- Update cost tracking regularly
