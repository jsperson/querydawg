# Frontend - Next.js Application

This directory contains the DataPrism frontend built with Next.js 14, TypeScript, and Tailwind CSS.

## Structure

```
frontend/
├── app/                     # Next.js 14 app directory
│   ├── page.tsx            # Landing page
│   ├── layout.tsx          # Root layout
│   ├── query/              # Query interface
│   ├── comparison/         # Side-by-side comparison
│   └── dashboard/          # Evaluation dashboard
├── components/             # React components
│   ├── QueryInput.tsx
│   ├── SQLDisplay.tsx
│   ├── ResultsTable.tsx
│   └── ContextViewer.tsx
├── lib/                    # Utilities
│   ├── api.ts             # Backend API client
│   └── utils.ts           # Helper functions
├── public/                 # Static assets
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

2. Set up environment variables:
```bash
cp ../.env.example .env.local
# Edit .env.local with your backend API URL
```

3. Run development server:
```bash
npm run dev
```

Visit http://localhost:3000

## Build

```bash
npm run build
npm start  # Production server
```

## Deployment

Deployed to Vercel automatically when pushed to GitHub (main branch).

Vercel will auto-detect Next.js and configure appropriately.
