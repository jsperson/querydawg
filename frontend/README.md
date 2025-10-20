# Frontend - Next.js Application

This directory contains the DataPrism frontend built with Next.js 14, TypeScript, shadcn/ui, and Tailwind CSS.

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
├── lib/                    # Utilities
│   ├── api.ts             # Backend API client
│   └── utils.ts           # Helper functions (includes cn() from shadcn)
├── public/                 # Static assets
├── components.json         # shadcn/ui configuration
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

4. Set up environment variables:
```bash
cp ../.env.example .env.local
# Edit .env.local with your backend API URL
```

5. Run development server:
```bash
npm run dev
```

Visit http://localhost:3000

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
