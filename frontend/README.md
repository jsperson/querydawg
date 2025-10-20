# Frontend - Next.js Application

This directory contains the DataPrism frontend built with Next.js 14, TypeScript, shadcn/ui, Tailwind CSS, and Drizzle ORM.

## Structure

```
frontend/
├── app/                     # Next.js 14 app directory
│   ├── page.tsx            # Landing page
│   ├── layout.tsx          # Root layout
│   ├── query/              # Query interface
│   ├── comparison/         # Side-by-side comparison
│   └── dashboard/          # Evaluation dashboard
├── components/
│   ├── ui/                 # shadcn/ui components (auto-generated)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── table.tsx
│   │   └── ...
│   ├── QueryInput.tsx      # Custom components
│   ├── SQLDisplay.tsx
│   ├── ResultsTable.tsx
│   └── ContextViewer.tsx
├── drizzle/                # Drizzle ORM
│   ├── schema.ts          # Database schema definitions
│   └── migrations/        # Database migrations
├── lib/
│   ├── db.ts              # Drizzle database client
│   ├── api.ts             # Backend API client
│   └── utils.ts           # Helper functions (includes cn() from shadcn)
├── public/                 # Static assets
├── components.json         # shadcn/ui configuration
├── drizzle.config.ts       # Drizzle ORM configuration
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Initialize shadcn/ui (first time only):
```bash
npx shadcn-ui@latest init
```

This will:
- Set up Tailwind CSS configuration
- Configure path aliases (@/components)
- Create components.json configuration
- Set up CSS variables for theming

When prompted, select:
- Style: **Default**
- Base color: **Slate** (or your preference)
- CSS variables: **Yes**

3. Add shadcn/ui components as needed:
```bash
# Example: Add commonly used components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add table
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add select
npx shadcn-ui@latest add tabs
```

4. Install and configure Drizzle ORM:
```bash
# Install Drizzle ORM and PostgreSQL driver
npm install drizzle-orm postgres
npm install -D drizzle-kit

# Generate migrations (after defining schema)
npx drizzle-kit generate:pg

# Run migrations
npx drizzle-kit push:pg
```

5. Set up environment variables:
```bash
cp ../.env.example .env.local
# Edit .env.local with:
# - NEXT_PUBLIC_API_URL (backend API)
# - DATABASE_URL (Supabase PostgreSQL - Transaction Pooler)
```

6. Run development server:
```bash
npm run dev
```

Visit http://localhost:3000

## Database ORM

This project uses **Drizzle ORM** - a TypeScript-first ORM for accessing Supabase PostgreSQL from Next.js.

**Why Drizzle ORM?**
- ✅ **TypeScript-first** - Full type safety with schema inference
- ✅ **SQL-like syntax** - Intuitive queries that feel like SQL
- ✅ **Lightweight** - No heavy runtime, minimal overhead
- ✅ **Great DX** - Auto-completion, type checking at build time
- ✅ **Perfect for Next.js 14** - Works seamlessly with Server Components and API routes
- ✅ **Supabase compatible** - Excellent PostgreSQL support

**Basic Usage Example:**
```typescript
// drizzle/schema.ts
import { pgTable, serial, text, timestamp } from 'drizzle-orm/pg-core';

export const documents = pgTable('documents', {
  id: serial('id').primaryKey(),
  database_name: text('database_name').notNull(),
  content: text('content').notNull(),
  created_at: timestamp('created_at').defaultNow(),
});

// lib/db.ts
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

const client = postgres(process.env.DATABASE_URL!);
export const db = drizzle(client);

// Usage in API route or Server Component
import { db } from '@/lib/db';
import { documents } from '@/drizzle/schema';

const results = await db.select().from(documents).where(eq(documents.database_name, 'concert_singer'));
```

**Resources:**
- [Drizzle ORM Documentation](https://orm.drizzle.team)
- [PostgreSQL Guide](https://orm.drizzle.team/docs/get-started-postgresql)
- [Supabase Integration](https://orm.drizzle.team/docs/tutorials/drizzle-with-supabase)

## UI Components

This project uses **shadcn/ui** - a collection of re-usable components built with Radix UI and Tailwind CSS.

**Why shadcn/ui?**
- ✅ Copy components directly into your project (you own the code)
- ✅ Fully customizable and accessible (Radix UI primitives)
- ✅ Beautiful default styling with Tailwind CSS
- ✅ TypeScript support
- ✅ Perfect for Next.js 14

**Resources:**
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [Component Examples](https://ui.shadcn.com/examples)
- [Themes](https://ui.shadcn.com/themes)

## Build

```bash
npm run build
npm start  # Production server
```

## Deployment

Deployed to Vercel automatically when pushed to GitHub (main branch).

Vercel will auto-detect Next.js and configure appropriately.
