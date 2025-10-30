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

interface BenchmarkResult {
  run_id: string;
  question_id: string;
  database: string;
  question: string;
  gold_sql: string;
  difficulty: string | null;
  baseline_sql: string | null;
  baseline_exact_match: boolean | null;
  baseline_exec_match: boolean | null;
  baseline_error: string | null;
  enhanced_sql: string | null;
  enhanced_exact_match: boolean | null;
  enhanced_exec_match: boolean | null;
  enhanced_error: string | null;
}

export default function BenchmarkResultsPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [summary, setSummary] = useState<BenchmarkSummary | null>(null);
  const [results, setResults] = useState<BenchmarkResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<BenchmarkResult | null>(null);
  const [showFailuresOnly, setShowFailuresOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingResults, setIsLoadingResults] = useState(false);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const loadResults = async () => {
    setIsLoadingResults(true);
    setError('');
    try {
      const params_str = new URLSearchParams({
        failures_only: showFailuresOnly.toString(),
        page_size: '1000'
      });
      const response = await fetch(`/api/benchmark/run/${params.id}/results?${params_str}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      console.log('Loaded results:', data);
      setResults(data.results || []);
      if (!data.results || data.results.length === 0) {
        setError('No results found for this benchmark run');
      }
    } catch (err) {
      console.error('Failed to load results:', err);
      const errorMessage = err instanceof Error ? err.message : JSON.stringify(err);
      setError(`Failed to load results: ${errorMessage}`);
    } finally {
      setIsLoadingResults(false);
    }
  };

  const handleCancelRun = async () => {
    if (!confirm('Are you sure you want to stop this benchmark run?')) {
      return;
    }

    try {
      const response = await fetch(`/api/benchmark/run/${params.id}/cancel`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to cancel benchmark');
      }

      // Refresh summary
      await loadSummary();
      setError('Benchmark cancelled successfully');
    } catch (err) {
      setError(`Failed to cancel: ${err instanceof Error ? err.message : 'Unknown error'}`);
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
              <div className="flex items-center gap-2">
                {getStatusBadge(summary.status)}
                {isRunning && (
                  <Button size="sm" variant="destructive" onClick={handleCancelRun}>
                    Stop
                  </Button>
                )}
              </div>
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

            {/* SQL Results Viewer */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>SQL Results</CardTitle>
                    <CardDescription>View detailed SQL for each question</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setShowFailuresOnly(!showFailuresOnly);
                        if (results.length > 0) {
                          loadResults();
                        }
                      }}
                    >
                      {showFailuresOnly ? 'Show All' : 'Show Failures Only'}
                    </Button>
                    <Button onClick={loadResults} disabled={isLoadingResults}>
                      {isLoadingResults ? 'Loading...' : results.length > 0 ? 'Refresh Results' : 'Load Results'}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {error && results.length === 0 && (
                  <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md mb-4">
                    {error}
                  </div>
                )}
                {results.length === 0 && !error ? (
                  <p className="text-center text-muted-foreground py-8">
                    Click &quot;Load Results&quot; to view detailed SQL for each question
                  </p>
                ) : results.length > 0 ? (
                  <div className="grid grid-cols-2 gap-6">
                    {/* Question List */}
                    <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
                      <h3 className="font-semibold mb-3">Questions ({results.length})</h3>
                      {results.map((result) => (
                          <div
                            key={result.question_id}
                            onClick={() => setSelectedResult(result)}
                            className={`p-3 rounded-md border cursor-pointer transition-colors ${
                              selectedResult?.question_id === result.question_id
                                ? 'bg-primary text-primary-foreground border-primary'
                                : 'hover:bg-muted border-border'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-2 mb-1">
                              <span className="text-xs font-mono text-muted-foreground">
                                {result.question_id}
                              </span>
                              <div className="flex gap-1">
                                {summary.run_type !== 'enhanced' && (
                                  <Badge
                                    className={`text-xs ${
                                      result.baseline_exec_match
                                        ? 'bg-green-600'
                                        : 'bg-red-600'
                                    }`}
                                  >
                                    B
                                  </Badge>
                                )}
                                {summary.run_type !== 'baseline' && (
                                  <Badge
                                    className={`text-xs ${
                                      result.enhanced_exec_match
                                        ? 'bg-green-600'
                                        : 'bg-red-600'
                                    }`}
                                  >
                                    E
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <p className="text-sm line-clamp-2">{result.question}</p>
                            <p className="text-xs text-muted-foreground mt-1">{result.database}</p>
                          </div>
                      ))}
                    </div>

                    {/* SQL Comparison View */}
                    <div className="space-y-4">
                      {selectedResult ? (
                        <>
                          <div>
                            <h3 className="font-semibold mb-2">Question</h3>
                            <p className="text-sm bg-muted p-3 rounded-md">{selectedResult.question}</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              Database: {selectedResult.database} • ID: {selectedResult.question_id}
                            </p>
                          </div>

                          {/* Gold SQL */}
                          <div>
                            <h3 className="font-semibold mb-2">Gold SQL (Expected)</h3>
                            <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
                              {selectedResult.gold_sql}
                            </pre>
                          </div>

                          {/* Baseline SQL */}
                          {summary.run_type !== 'enhanced' && (
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold">Baseline SQL</h3>
                                <div className="flex gap-2">
                                  {selectedResult.baseline_exact_match !== null && (
                                    <Badge className={selectedResult.baseline_exact_match ? 'bg-green-600' : 'bg-red-600'}>
                                      Exact: {selectedResult.baseline_exact_match ? 'Match' : 'No Match'}
                                    </Badge>
                                  )}
                                  {selectedResult.baseline_exec_match !== null && (
                                    <Badge className={selectedResult.baseline_exec_match ? 'bg-green-600' : 'bg-red-600'}>
                                      Exec: {selectedResult.baseline_exec_match ? 'Match' : 'No Match'}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                              {selectedResult.baseline_sql ? (
                                <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
                                  {selectedResult.baseline_sql}
                                </pre>
                              ) : (
                                <p className="text-sm text-muted-foreground italic">No SQL generated</p>
                              )}
                              {selectedResult.baseline_error && (
                                <div className="mt-2 text-xs text-red-600 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                                  Error: {selectedResult.baseline_error}
                                </div>
                              )}
                            </div>
                          )}

                          {/* Enhanced SQL */}
                          {summary.run_type !== 'baseline' && (
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold">Enhanced SQL</h3>
                                <div className="flex gap-2">
                                  {selectedResult.enhanced_exact_match !== null && (
                                    <Badge className={selectedResult.enhanced_exact_match ? 'bg-green-600' : 'bg-red-600'}>
                                      Exact: {selectedResult.enhanced_exact_match ? 'Match' : 'No Match'}
                                    </Badge>
                                  )}
                                  {selectedResult.enhanced_exec_match !== null && (
                                    <Badge className={selectedResult.enhanced_exec_match ? 'bg-green-600' : 'bg-red-600'}>
                                      Exec: {selectedResult.enhanced_exec_match ? 'Match' : 'No Match'}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                              {selectedResult.enhanced_sql ? (
                                <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
                                  {selectedResult.enhanced_sql}
                                </pre>
                              ) : (
                                <p className="text-sm text-muted-foreground italic">No SQL generated</p>
                              )}
                              {selectedResult.enhanced_error && (
                                <div className="mt-2 text-xs text-red-600 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                                  Error: {selectedResult.enhanced_error}
                                </div>
                              )}
                            </div>
                          )}
                        </>
                      ) : (
                        <p className="text-center text-muted-foreground py-20">
                          Select a question from the list to view SQL details
                        </p>
                      )}
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </main>
  );
}
