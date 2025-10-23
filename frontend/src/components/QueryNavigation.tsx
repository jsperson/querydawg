'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function QueryNavigation() {
  const pathname = usePathname();

  const tabs = [
    {
      name: 'Compare',
      href: '/compare',
      description: 'Side-by-side comparison'
    },
    {
      name: 'Baseline',
      href: '/baseline',
      description: 'Schema only (GPT-4o-mini)'
    },
    {
      name: 'Enhanced',
      href: '/enhanced',
      description: 'Schema + Semantic Layer (GPT-4o)'
    },
  ];

  return (
    <div className="border-b border-zinc-200 dark:border-zinc-800 mb-6">
      <nav className="flex gap-2" aria-label="Query mode navigation">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`
                px-4 py-3 text-sm font-medium border-b-2 transition-colors
                ${
                  isActive
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-zinc-300 dark:hover:border-zinc-700'
                }
              `}
            >
              <div className="flex items-center gap-2">
                <span>{tab.name}</span>
                <span className="text-xs text-muted-foreground hidden sm:inline">
                  {tab.description}
                </span>
              </div>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
