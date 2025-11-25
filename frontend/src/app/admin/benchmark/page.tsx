'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useAdminAuth } from '@/components/AdminLoginModal';
import { adminAuth } from '@/lib/admin';

interface BenchmarkRun {
  run_id: string;
  name: string;
  run_type: string;
  data_source: string;
  status: string;
  total_questions: number;
  completed: number;
  failed: number;
  baseline_exec_match_rate: number | null;
  enhanced_exec_match_rate: number | null;
  created_at: string;
}

export default function BenchmarkControlPanel() {
  const router = useRouter();
  const { isAdmin, isLoading: isLoadingAuth, adminRequired, requestAdminAccess, AdminModal } = useAdminAuth();

  // Form state
  const [name, setName] = useState('');
  const [runType, setRunType] = useState<'baseline' | 'enhanced' | 'both'>('both');
  const [dataSource, setDataSource] = useState<'supabase' | 'turso'>('turso');
  const [questionLimit, setQuestionLimit] = useState<number | null>(null);
  const [selectedDatabase, setSelectedDatabase] = useState<string>('all');

  // UI state
  const [isStarting, setIsStarting] = useState(false);
  const [isLoadingRuns, setIsLoadingRuns] = useState(true);
  const [isLoadingDatabases, setIsLoadingDatabases] = useState(true);
  const [runs, setRuns] = useState<BenchmarkRun[]>([]);
  const [databases, setDatabases] = useState<string[]>([]);
  const [error, setError] = useState('');

  // Load recent runs
  useEffect(() => {
    loadRuns();
    const interval = setInterval(loadRuns, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  // Load databases on mount
  useEffect(() => {
    loadDatabases();
  }, []);

  const loadRuns = async () => {
    try {
      const response = await fetch('/api/benchmark/runs');
      if (!response.ok) throw new Error('Failed to load runs');
      const data = await response.json();
      setRuns(data);
      setError('');
    } catch {
      setError('Failed to load benchmark runs');
    } finally {
      setIsLoadingRuns(false);
    }
  };

  const loadDatabases = async () => {
    try {
      const response = await fetch('/api/databases');
      if (!response.ok) throw new Error('Failed to load databases');
      const data = await response.json();
      setDatabases(data.databases);
    } catch {
      setError('Failed to load databases');
    } finally {
      setIsLoadingDatabases(false);
    }
  };

  const doStartBenchmark = async () => {
    setIsStarting(true);
    setError('');

    try {
      const config = {
        name: name.trim(),
        run_type: runType,
        data_source: dataSource, // New: Supabase or Turso
        databases: selectedDatabase === 'all' ? null : [selectedDatabase], // null = all databases
        question_limit: questionLimit
      };

      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      const password = adminAuth.getPassword();
      if (password) {
        headers['X-Admin-Password'] = password;
      }

      const response = await fetch('/api/benchmark/run', {
        method: 'POST',
        headers,
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start benchmark');
      }

      const result = await response.json();

      // Reset form
      setName('');
      setQuestionLimit(null);

      // Refresh runs list
      await loadRuns();

      // Show success message that stays visible
      setError(`✅ Success! Benchmark started. Processing ${result.question_count} questions. Refresh the page to see progress.`);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start benchmark';
      console.error('Benchmark start error:', err);
      setError(`❌ Error: ${errorMessage}`);
    } finally {
      setIsStarting(false);
    }
  };

  const handleStartBenchmark = () => {
    if (!name.trim()) {
      setError('Please enter a name for this benchmark run');
      return;
    }

    // Check if admin auth is required
    if (adminRequired && !isAdmin) {
      requestAdminAccess(doStartBenchmark);
      return;
    }

    doStartBenchmark();
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

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-800">
      {AdminModal}
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">Benchmark Control Panel</h1>
            <p className="text-lg text-muted-foreground">
              Run Spider 1.0 evaluation benchmarks to compare baseline vs enhanced approaches
            </p>
          </div>
          <div className="flex gap-2 items-center">
            {adminRequired && (
              <Badge variant={isAdmin ? "default" : "secondary"} className="mr-2">
                {isLoadingAuth ? 'Checking...' : isAdmin ? 'Admin' : 'View Only'}
              </Badge>
            )}
            {adminRequired && !isAdmin && (
              <Button onClick={requestAdminAccess} variant="outline" size="sm">
                Login as Admin
              </Button>
            )}
            <Button onClick={() => router.push('/compare')} variant="outline">
              Back to Compare Mode
            </Button>
          </div>
        </div>

        {/* Start New Benchmark */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Start New Benchmark</CardTitle>
            <CardDescription>
              Configure and launch a Spider 1.0 benchmark evaluation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Name */}
            <div>
              <Label htmlFor="name">Benchmark Name</Label>
              <Input
                id="name"
                placeholder="e.g., Full Spider 1.0 Evaluation"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isStarting}
              />
            </div>

            {/* Run Type */}
            <div>
              <Label htmlFor="runType">Run Type</Label>
              <Select
                value={runType}
                onValueChange={(value: 'baseline' | 'enhanced' | 'both') => setRunType(value)}
                disabled={isStarting}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="baseline">Baseline Only (schema only)</SelectItem>
                  <SelectItem value="enhanced">Enhanced Only (+ semantic layer)</SelectItem>
                  <SelectItem value="both">Both (compare side-by-side)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Data Source */}
            <div>
              <Label htmlFor="dataSource">Database Source</Label>
              <Select
                value={dataSource}
                onValueChange={(value: 'supabase' | 'turso') => setDataSource(value)}
                disabled={isStarting}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="supabase">Supabase (PostgreSQL)</SelectItem>
                  <SelectItem value="turso">Turso (SQLite) ⚡</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                {dataSource === 'turso'
                  ? '⚡ Turso: Native Spider format - eliminates 84 gold SQL conversion failures'
                  : 'PostgreSQL: Requires SQLite→PostgreSQL conversion (84 known conversion issues)'
                }
              </p>
            </div>

            {/* Database Selector */}
            <div>
              <Label htmlFor="database">Database</Label>
              <Select
                value={selectedDatabase}
                onValueChange={setSelectedDatabase}
                disabled={isStarting || isLoadingDatabases}
              >
                <SelectTrigger>
                  <SelectValue placeholder={isLoadingDatabases ? "Loading databases..." : "Select database"} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Databases (20 databases)</SelectItem>
                  {databases.map((db) => (
                    <SelectItem key={db} value={db}>
                      {db}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                Select a single database or run on all 20 databases
              </p>
            </div>

            {/* Question Limit */}
            <div>
              <Label htmlFor="questionLimit">Question Limit (optional)</Label>
              <Input
                id="questionLimit"
                type="number"
                placeholder="Leave empty for all 1,034 questions"
                value={questionLimit ?? ''}
                onChange={(e) => setQuestionLimit(e.target.value ? parseInt(e.target.value) : null)}
                disabled={isStarting}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Tip: Use a small limit (e.g., 50) for quick tests
              </p>
            </div>

            {/* Error/Success Display */}
            {error && (
              <div className={`px-4 py-3 rounded-md border ${
                error.startsWith('✅')
                  ? 'bg-green-50 text-green-800 border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800'
                  : 'bg-destructive/10 text-destructive border-destructive/20'
              }`}>
                <div className="flex justify-between items-start gap-2">
                  <div className="flex-1 whitespace-pre-wrap">{error}</div>
                  <button
                    onClick={() => setError('')}
                    className="text-current opacity-70 hover:opacity-100 font-bold"
                  >
                    ✕
                  </button>
                </div>
              </div>
            )}

            {/* Start Button */}
            <Button
              onClick={handleStartBenchmark}
              disabled={isStarting || !name.trim()}
              className="w-full"
              size="lg"
            >
              {isStarting ? 'Starting Benchmark...' : adminRequired && !isAdmin ? 'Login & Start Benchmark' : 'Start Benchmark'}
            </Button>

            <p className="text-sm text-muted-foreground text-center">
              Budget limit: $5.00 per run | Estimated time: 20-30 minutes for full dataset
            </p>
          </CardContent>
        </Card>

        {/* Recent Runs */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Benchmark Runs</CardTitle>
            <CardDescription>
              Click on a run to view detailed results
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingRuns ? (
              <p className="text-center text-muted-foreground py-8">Loading runs...</p>
            ) : runs.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                No benchmark runs yet. Start one above!
              </p>
            ) : (
              <div className="rounded-md border overflow-hidden">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Source</TableHead>
                        <TableHead>Progress</TableHead>
                        <TableHead>Baseline Accuracy</TableHead>
                        <TableHead>Enhanced Accuracy</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {runs.map((run) => (
                        <TableRow
                          key={run.run_id}
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => router.push(`/admin/benchmark/${run.run_id}`)}
                        >
                          <TableCell className="font-medium">{run.name}</TableCell>
                          <TableCell>{getStatusBadge(run.status)}</TableCell>
                          <TableCell className="capitalize">{run.run_type}</TableCell>
                          <TableCell className="font-semibold uppercase text-xs">{run.data_source}</TableCell>
                          <TableCell>
                            {run.completed}/{run.total_questions}
                            {run.failed > 0 && <span className="text-red-600 ml-1">({run.failed} failed)</span>}
                          </TableCell>
                          <TableCell>
                            {run.baseline_exec_match_rate !== null
                              ? `${(run.baseline_exec_match_rate * 100).toFixed(1)}%`
                              : '-'}
                          </TableCell>
                          <TableCell>
                            {run.enhanced_exec_match_rate !== null
                              ? `${(run.enhanced_exec_match_rate * 100).toFixed(1)}%`
                              : '-'}
                          </TableCell>
                          <TableCell>
                            {new Date(run.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                router.push(`/admin/benchmark/${run.run_id}`);
                              }}
                            >
                              View Details
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
