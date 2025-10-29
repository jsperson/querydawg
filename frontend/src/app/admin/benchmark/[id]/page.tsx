'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface BenchmarkSummary {
  run_id: string;
  name: string;
  run_type: string;
  status: string;
  status_reason: string | null;
  total_questions: number;
  completed: number;
  failed: number;
  baseline_exact_match_rate: number | null;
  baseline_exec_match_rate: number | null;
  baseline_total_cost: number | null;
  enhanced_exact_match_rate: number | null;
  enhanced_exec_match_rate: number | null;
  enhanced_total_cost: number | null;
  total_time_ms: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export default function BenchmarkResultsPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [summary, setSummary] = useState<BenchmarkSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadSummary();

    // Poll for updates if status is pending or running
    const interval = setInterval(() => {
      if (summary && (summary.status === 'pending' || summary.status === 'running')) {
        loadSummary();
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [params.id, summary?.status]);

  const loadSummary = async () => {
    try {
      const response = await fetch(`/api/benchmark/run/${params.id}/summary`);
      if (!response.ok) throw new Error('Failed to load summary');
      const data = await response.json();
      setSummary(data);
      setError('');
    } catch {
      setError('Failed to load benchmark results');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, string> = {
      pending: 'bg-yellow-500',
      running: 'bg-blue-500',
      completed: 'bg-green-600',
      failed: 'bg-red-600',
      cancelled: 'bg-gray-500'
    };

    return (
      <Badge className={variants[status] || 'bg-gray-500'}>
        {status.toUpperCase()}
      </Badge>
    );
  };

  const formatDuration = (ms: number | null): string => {
    if (!ms) return '-';
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  if (isLoading) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-800">
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          <p className="text-center text-muted-foreground">Loading benchmark results...</p>
        </div>
      </main>
    );
  }

  if (error || !summary) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-800">
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md">
            {error || 'Benchmark not found'}
          </div>
          <Button onClick={() => router.push('/admin/benchmark')} className="mt-4">
            Back to Control Panel
          </Button>
        </div>
      </main>
    );
  }

  const progress = summary.total_questions > 0
    ? (summary.completed / summary.total_questions) * 100
    : 0;

  const isRunning = summary.status === 'pending' || summary.status === 'running';

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-800">
      <div className="container mx-auto px-4 py-8 max-w-7xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">{summary.name}</h1>
            <p className="text-lg text-muted-foreground">
              Benchmark Results • {summary.run_type.charAt(0).toUpperCase() + summary.run_type.slice(1)} Mode
            </p>
          </div>
          <Button onClick={() => router.push('/admin/benchmark')} variant="outline">
            Back to Control Panel
          </Button>
        </div>

        {/* Status Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Run Status</CardTitle>
              {getStatusBadge(summary.status)}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {isRunning && (
              <>
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium">Progress</span>
                    <span className="text-sm text-muted-foreground">
                      {summary.completed} / {summary.total_questions} questions
                    </span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>
                <p className="text-sm text-muted-foreground">
                  ⏳ Benchmark is currently running... This page will auto-refresh.
                </p>
              </>
            )}

            {!isRunning && (
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Completed</p>
                  <p className="text-2xl font-bold">{summary.completed}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Failed</p>
                  <p className="text-2xl font-bold text-red-600">{summary.failed}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Duration</p>
                  <p className="text-2xl font-bold">{formatDuration(summary.total_time_ms)}</p>
                </div>
              </div>
            )}

            {summary.status_reason && (
              <div className="bg-muted p-3 rounded-md">
                <p className="text-sm">
                  <span className="font-semibold">Reason:</span> {summary.status_reason}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Summary - Only show if completed */}
        {summary.status === 'completed' && (
          <>
            {/* Baseline Results */}
            {(summary.run_type === 'baseline' || summary.run_type === 'both') && (
              <Card>
                <CardHeader>
                  <CardTitle>Baseline Results</CardTitle>
                  <CardDescription>Schema-only approach (no semantic layer)</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-6">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Exact Match Rate</p>
                      <p className="text-3xl font-bold">
                        {summary.baseline_exact_match_rate !== null
                          ? `${(summary.baseline_exact_match_rate * 100).toFixed(1)}%`
                          : '-'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Execution Match Rate</p>
                      <p className="text-3xl font-bold">
                        {summary.baseline_exec_match_rate !== null
                          ? `${(summary.baseline_exec_match_rate * 100).toFixed(1)}%`
                          : '-'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Total Cost</p>
                      <p className="text-3xl font-bold">
                        {summary.baseline_total_cost !== null
                          ? `$${summary.baseline_total_cost.toFixed(4)}`
                          : '-'}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Enhanced Results */}
            {(summary.run_type === 'enhanced' || summary.run_type === 'both') && (
              <Card>
                <CardHeader>
                  <CardTitle>Enhanced Results</CardTitle>
                  <CardDescription>With semantic layer context</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-6">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Exact Match Rate</p>
                      <p className="text-3xl font-bold">
                        {summary.enhanced_exact_match_rate !== null
                          ? `${(summary.enhanced_exact_match_rate * 100).toFixed(1)}%`
                          : '-'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Execution Match Rate</p>
                      <p className="text-3xl font-bold">
                        {summary.enhanced_exec_match_rate !== null
                          ? `${(summary.enhanced_exec_match_rate * 100).toFixed(1)}%`
                          : '-'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Total Cost</p>
                      <p className="text-3xl font-bold">
                        {summary.enhanced_total_cost !== null
                          ? `$${summary.enhanced_total_cost.toFixed(4)}`
                          : '-'}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Comparison - Only if both run */}
            {summary.run_type === 'both' &&
             summary.baseline_exact_match_rate !== null &&
             summary.enhanced_exact_match_rate !== null && (
              <Card>
                <CardHeader>
                  <CardTitle>Improvement Analysis</CardTitle>
                  <CardDescription>Enhanced vs Baseline</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Accuracy Improvement</p>
                      <p className="text-3xl font-bold text-green-600">
                        +{((summary.enhanced_exact_match_rate - summary.baseline_exact_match_rate) * 100).toFixed(1)}%
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        ({(summary.baseline_exact_match_rate * 100).toFixed(1)}% → {(summary.enhanced_exact_match_rate * 100).toFixed(1)}%)
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Cost Difference</p>
                      <p className="text-3xl font-bold">
                        {summary.enhanced_total_cost && summary.baseline_total_cost
                          ? `+$${(summary.enhanced_total_cost - summary.baseline_total_cost).toFixed(4)}`
                          : '-'}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Additional cost for semantic layer
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Metadata */}
            <Card>
              <CardHeader>
                <CardTitle>Run Metadata</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Run ID:</span>
                  <span className="font-mono">{summary.run_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Created:</span>
                  <span>{new Date(summary.created_at).toLocaleString()}</span>
                </div>
                {summary.started_at && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Started:</span>
                    <span>{new Date(summary.started_at).toLocaleString()}</span>
                  </div>
                )}
                {summary.completed_at && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Completed:</span>
                    <span>{new Date(summary.completed_at).toLocaleString()}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </main>
  );
}
