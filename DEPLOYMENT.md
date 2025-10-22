# DataPrism Deployment Guide

This guide covers deploying the DataPrism application to production.

**Status:** Week 1 deployments tested and verified. Deployments can be activated on-demand.

## Architecture

**Week 1 (Current - Baseline):**
- **Backend**: FastAPI application on Railway
- **Frontend**: Next.js application on Vercel
- **Database**: Local SQLite files (19 Spider databases)
- **LLM**: OpenAI GPT-4o-mini via API

**Week 2+ (Planned - Enhanced):**
- **Database**: Migrate to Supabase PostgreSQL (for centralized access)
- **Vector DB**: Pinecone (for semantic layer storage and retrieval)
- **LLM**: Multi-provider support (OpenAI, Anthropic, Ollama)

## Backend Deployment (Railway)

### Prerequisites

- GitHub repository connected
- Railway account: https://railway.app
- Environment variables ready (from `.env`)

### Step 1: Create Railway Project

1. Go to https://railway.app and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub account
5. Select the `dataprism` repository
6. Railway will automatically detect the `railway.toml` configuration

### Step 2: Configure Environment Variables

In the Railway dashboard, go to your project > Variables tab and add:

**Week 1 (Required - Minimal Setup):**
```bash
# LLM API
OPENAI_API_KEY=sk-proj-xxxxx

# Backend Authentication
API_KEY=<generate-secure-key>

# LLM Provider (optional, defaults to openai)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

**Week 2+ (Additional - For Enhanced Features):**
```bash
# Database (for centralized Spider DBs)
DATABASE_URL=postgresql://postgres.xxxxx@aws-0-us-east-2.pooler.supabase.com:6543/postgres

# Vector Database (for semantic layer)
PINECONE_API_KEY=pcsk_xxxxx
PINECONE_HOST=https://xxxxx.svc.aped-4627-b74a.pinecone.io

# Additional LLM Providers
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-vercel-app.vercel.app,https://www.yourdomain.com
```

**Important**:
- Generate a secure `API_KEY` for production: `openssl rand -hex 32`
- For Week 1, databases are included in the deployment as SQLite files
- Week 2+: Use Supabase **Transaction Pooler** URL (port 6543), not Direct Connection
- Add your Vercel domain to `CORS_ORIGINS` after frontend deployment

### Step 3: Deploy

Railway will automatically deploy when you push to the `main` branch.

To deploy manually:
1. Go to your Railway project
2. Click "Deploy" or "Redeploy"

### Step 4: Get Your Railway URL

After deployment:
1. Go to Settings > Networking
2. Click "Generate Domain"
3. Your backend will be available at: `https://your-project.up.railway.app`
4. Test it: `curl https://your-project.up.railway.app/api/health`

### Step 5: Configure Custom Domain (Optional)

1. In Railway Settings > Networking
2. Click "Custom Domain"
3. Add your domain (e.g., `api.yourdomain.com`)
4. Add the CNAME record to your DNS provider

## Frontend Deployment (Vercel)

### Prerequisites

- Vercel account: https://vercel.com
- Railway backend deployed and URL ready

### Step 1: Create Vercel Project

1. Go to https://vercel.com and sign in
2. Click "Add New Project"
3. Import your GitHub repository
4. Vercel will auto-detect Next.js

### Step 2: Configure Build Settings

Vercel should auto-detect Next.js. Verify:
- **Framework Preset**: Next.js
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

### Step 3: Configure Environment Variables

Add these environment variables in Vercel project settings:

```bash
# Backend API URL - use your Railway domain
NEXT_PUBLIC_BACKEND_URL=https://your-project.up.railway.app

# API Key for backend authentication (server-side only, NOT public)
BACKEND_API_KEY=<same-as-backend-api-key>
```

**Important:**
- `NEXT_PUBLIC_BACKEND_URL` is public (can be seen by browser)
- `BACKEND_API_KEY` is server-side only (used in API routes, never exposed to browser)
- Do NOT use `NEXT_PUBLIC_` prefix for API keys - they would be exposed to clients!

### Step 4: Deploy

1. Click "Deploy"
2. Vercel will build and deploy automatically
3. Your frontend will be available at: `https://your-project.vercel.app`

### Step 5: Update Backend CORS

Update Railway environment variable:
```bash
CORS_ORIGINS=https://your-project.vercel.app,https://www.yourdomain.com
```

Redeploy the backend for CORS changes to take effect.

### Step 6: Configure Custom Domain (Optional)

1. In Vercel Project Settings > Domains
2. Add your domain (e.g., `www.yourdomain.com`)
3. Follow Vercel's instructions to update DNS

## Testing Production Deployment

### Backend Health Check
```bash
curl https://your-project.up.railway.app/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-10-21T15:00:00.000000"
}
```

### Backend Databases Endpoint
```bash
curl -H "X-API-Key: your-api-key" \
  https://your-project.up.railway.app/api/databases
```

Expected response:
```json
{
  "databases": ["world_1", "car_1", ...],
  "count": 19
}
```

### Frontend
Visit `https://your-project.vercel.app` in your browser.

## Continuous Deployment

Both Railway and Vercel support automatic deployment:

- **Railway**: Deploys backend on push to `main` branch
- **Vercel**: Deploys frontend on push to `main` branch
- **Preview Deployments**: Both create preview deployments for pull requests

## Monitoring

### Railway Logs
- Go to Railway project > Deployments
- Click on a deployment to view logs
- Real-time logs available

### Vercel Logs
- Go to Vercel project > Deployments
- Click on a deployment > Functions tab
- View function logs and analytics

## Troubleshooting

### Railway Backend Issues

**Build fails**:
- Check `backend/requirements.txt` has all dependencies
- Verify Python version in `backend/requirements.txt` (should be 3.11+)

**Runtime errors**:
- Check Railway logs for errors
- Verify all environment variables are set
- Test DATABASE_URL connection from Railway console

**Connection timeouts**:
- Ensure using Supabase Transaction Pooler (port 6543)
- Check Supabase connection limits

### Vercel Frontend Issues

**Build fails**:
- Check `frontend/package.json` dependencies
- Verify Node.js version compatibility
- Check build logs for errors

**ESLint errors during build**:

Vercel uses strict ESLint rules. Common issues and fixes:

1. **"'error' is defined but never used"** in catch blocks:
   ```typescript
   // ❌ Wrong - unused variable
   } catch (error) {
     return NextResponse.json({ detail: 'Error' }, { status: 500 });
   }

   // ✅ Correct - no parameter or use it
   } catch {
     return NextResponse.json({ detail: 'Error' }, { status: 500 });
   }

   // ✅ Also correct - actually use the error
   } catch (error) {
     console.error(error);
     return NextResponse.json({ detail: 'Error' }, { status: 500 });
   }
   ```

2. **"Unexpected any"**:
   ```typescript
   // ❌ Wrong - explicit any
   results: Record<string, any>[]

   // ✅ Correct - use unknown
   results: Record<string, unknown>[]
   ```

3. **Missing files blocked by .gitignore**:
   - Check root `.gitignore` doesn't accidentally block needed files
   - Example: `lib/` blocked `frontend/src/lib/` - add exception: `!frontend/src/lib/`

**API connection errors**:
- Verify `NEXT_PUBLIC_BACKEND_URL` points to Railway backend
- Check CORS settings in backend
- Verify API key is correct (`BACKEND_API_KEY`, not `NEXT_PUBLIC_API_KEY`)

## Security Checklist

- [ ] Generate secure `API_KEY` for production (not `dev-dataprism-api-key-2024`)
- [ ] Configure CORS to only allow your frontend domain
- [ ] Use environment variables for all secrets (never commit to git)
- [ ] Enable HTTPS (Railway and Vercel provide this automatically)
- [ ] Regularly rotate API keys
- [ ] Monitor Railway logs for suspicious activity
- [ ] Keep dependencies up to date

## Cost Monitoring

### Railway
- Free tier: 500 hours/month
- Monitor usage in Railway dashboard
- Set up billing alerts

### Vercel
- Free tier: 100GB bandwidth/month
- Monitor usage in Vercel dashboard
- Serverless function limits apply

### Supabase
- Free tier: 500MB database, 2GB bandwidth/month
- Monitor in Supabase dashboard
- Alternative: Xata.io (see project_plan.md)

### Pinecone
- Free tier: 1 index, limited storage
- Monitor in Pinecone dashboard

## Rollback Procedure

### Railway
1. Go to Deployments
2. Find previous successful deployment
3. Click "Redeploy"

### Vercel
1. Go to Deployments
2. Find previous deployment
3. Click "Promote to Production"

## Support

- Railway docs: https://docs.railway.app
- Vercel docs: https://vercel.com/docs
- Supabase docs: https://supabase.com/docs

## Deployment History

### Week 1 Deployments (October 2025)

**Backend - Railway:**
- Project: `dataprism-production`
- URL: `https://dataprism-production.up.railway.app`
- Status: ✅ Successfully deployed and tested
- Configuration: SQLite databases, OpenAI GPT-4o-mini, modular LLM architecture
- Health check: `/api/health`
- API docs: `/docs` and `/redoc`
- Databases loaded: 19 Spider datasets

**Frontend - Vercel:**
- Project: `dataprism`
- URL: `https://dataprism.vercel.app`
- Status: ✅ Successfully deployed and tested (deactivated for cost control)
- Configuration: Next.js 14 App Router, shadcn/ui, Tailwind CSS
- Features: Database selection, SQL generation, query execution, results display

**Testing Results:**
- ✅ Health endpoint responding
- ✅ Database listing working (19 databases)
- ✅ Schema extraction working
- ✅ Text-to-SQL generation functional
- ✅ SQL execution working with safety limits
- ✅ End-to-end flow tested successfully

**Known Issues Resolved:**
- ESLint strict mode errors (unused variables, explicit any)
- Database loading state UX (added loading indicators)
- Question field state management (clears on database change)
- Gitignore blocking frontend/src/lib/ (added exception)
