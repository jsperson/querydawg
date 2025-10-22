# Frontend - Next.js Application

This directory contains the DataPrism frontend built with Next.js 14 (App Router), TypeScript, and shadcn/ui.

**Status:** Week 1 Complete - Baseline query interface functional

## Tech Stack

- **Framework:** Next.js 14 with App Router
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui (Radix UI primitives)
- **Deployment:** Vercel (on-demand)

## Structure

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── layout.tsx            # Root layout with fonts
│   │   ├── page.tsx              # Main query interface
│   │   ├── globals.css           # Global styles + Tailwind
│   │   └── api/                  # Server-side API routes (proxies to backend)
│   │       ├── databases/
│   │       │   └── route.ts      # List databases
│   │       ├── schema/
│   │       │   └── [database]/
│   │       │       └── route.ts  # Get database schema
│   │       ├── text-to-sql/
│   │       │   └── baseline/
│   │       │       └── route.ts  # Generate SQL
│   │       └── execute/
│   │           └── route.ts      # Execute SQL queries
│   ├── components/
│   │   └── ui/                   # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── select.tsx
│   │       ├── table.tsx
│   │       ├── textarea.tsx
│   │       └── badge.tsx
│   └── lib/
│       ├── api.ts                # Backend API client
│       ├── api-types.ts          # TypeScript types matching backend
│       └── utils.ts              # Utility functions (cn)
├── public/                       # Static assets
├── .env.local                    # Environment variables (not in git)
├── .env.example                  # Environment variable template
├── package.json                  # Dependencies
├── tailwind.config.ts            # Tailwind configuration
├── components.json               # shadcn/ui configuration
└── tsconfig.json                 # TypeScript configuration
```

## Features

### Current (Week 1)
- **Database Selection:** Dropdown with 19 Spider databases
- **Natural Language Input:** Textarea for questions
- **SQL Generation:** Real-time generation with GPT-4o-mini
- **SQL Display:** Syntax-highlighted SQL code display
- **Explanation:** Human-readable explanation of generated SQL
- **Metadata Display:** Tokens used, cost, generation time, model
- **Query Execution:** Execute generated SQL with one click
- **Results Display:** Interactive table with query results
- **Loading States:** Visual feedback during API calls
- **Error Handling:** User-friendly error messages

### Planned (Week 2+)
- **Side-by-Side Comparison:** Baseline vs Enhanced with semantic layer
- **Database Schema Viewer:** Interactive schema exploration
- **Query History:** Save and revisit previous queries
- **Export Results:** Download query results as CSV/JSON

## Setup

### Prerequisites
- Node.js 18+
- npm/yarn/pnpm
- Backend running (local or deployed)

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your backend URL
```

Environment variables:
- `NEXT_PUBLIC_BACKEND_URL` - Backend API URL (default: Railway production)
- `BACKEND_API_KEY` - API key for backend authentication

3. Run development server:
```bash
npm run dev
```

Visit http://localhost:3000

### shadcn/ui Setup

shadcn/ui is already configured. To add more components:

```bash
npx shadcn-ui@latest add [component-name]
```

Example:
```bash
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add tabs
```

## API Routes

The frontend uses Next.js API routes to proxy requests to the backend. This approach:
- Keeps API keys secure (server-side only)
- Enables CORS handling
- Allows request/response transformation
- Works with Vercel serverless functions

All API routes are in `src/app/api/` and follow this pattern:
1. Receive request from client
2. Add `X-API-Key` header
3. Forward to backend
4. Return response to client

## Deployment

### Vercel (Production-Ready)

The frontend is configured for Vercel deployment and can be activated on-demand.

**Quick Deploy:**
1. Push to GitHub `main` branch
2. Vercel auto-deploys (if connected)
3. Environment variables configured in Vercel dashboard

**Production URL** (when active): `https://dataprism.vercel.app`

**Environment Variables (Vercel Dashboard):**
- `NEXT_PUBLIC_BACKEND_URL` - Railway backend URL
- `BACKEND_API_KEY` - Backend API key

**Build Settings:**
- Framework: Next.js
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`

### ESLint Configuration

The project uses strict ESLint rules:
- No unused variables (use `_` prefix or remove)
- No explicit `any` types (use `unknown`)
- Catch blocks without parameters allowed

## Development

### Type Safety

All API types are defined in `src/lib/api-types.ts` and match the backend Pydantic models:
- `DatabaseListResponse`
- `SchemaResponse` (with `TableInfo`, `ColumnInfo`, `ForeignKeyInfo`)
- `TextToSQLRequest` / `TextToSQLResponse`
- `ExecuteRequest` / `ExecuteResponse`
- `ErrorResponse`

### API Client

The `src/lib/api.ts` module provides a typed API client:

```typescript
import { api } from '@/lib/api';

// List databases
const dbs = await api.getDatabases();

// Generate SQL
const result = await api.generateSQL({
  question: "Show top 5 countries by population",
  database: "world_1"
});

// Execute SQL
const results = await api.executeSQL({
  sql: "SELECT * FROM country LIMIT 5",
  database: "world_1"
});
```

### Component Usage

Using shadcn/ui components:

```typescript
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    <Button onClick={handleClick}>Click Me</Button>
  </CardContent>
</Card>
```

## Testing

Run type checking:
```bash
npm run type-check
```

Run linter:
```bash
npm run lint
```

Build for production:
```bash
npm run build
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Radix UI Documentation](https://www.radix-ui.com)
