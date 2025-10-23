'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { QueryNavigation } from '@/components/QueryNavigation';
import type { TextToSQLResponse, ExecuteResponse } from '@/lib/api-types';

interface ComparisonResult {
  baseline: {
    sql?: TextToSQLResponse;
    execution?: ExecuteResponse;
    error?: string;
  };
  enhanced: {
    sql?: TextToSQLResponse;
    execution?: ExecuteResponse;
    error?: string;
  };
}

export default function ComparePage() {
  // State
  const [databases, setDatabases] = useState<string[]>([]);
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [isLoadingDatabases, setIsLoadingDatabases] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string>('');

  // Load databases on mount
  useEffect(() => {
    loadDatabases();
  }, []);

  const loadDatabases = async () => {
    try {
      setIsLoadingDatabases(true);
      const response = await api.getDatabases();
      setDatabases(response.databases);
      if (response.databases.length > 0) {
        setSelectedDatabase(response.databases[0]);
      }
      setError('');
    } catch {
      setError('Failed to load databases');
    } finally {
      setIsLoadingDatabases(false);
    }
  };

  const handleDatabaseChange = (newDatabase: string) => {
    setSelectedDatabase(newDatabase);
    setQuestion('');
    setResult(null);
    setError('');
  };

  const handleRun = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }
    if (!selectedDatabase) {
      setError('Please select a database');
      return;
    }

    setError('');
    setIsRunning(true);
    setResult(null);

    const request = {
      question: question.trim(),
      database: selectedDatabase,
    };

    const newResult: ComparisonResult = {
      baseline: {},
      enhanced: {},
    };

    // Run both baseline and enhanced in parallel
    await Promise.allSettled([
      // Baseline SQL generation and execution
      api
        .generateSQL(request)
        .then(async (sqlResponse) => {
          newResult.baseline.sql = sqlResponse;
          // Execute the SQL
          try {
            const executeResponse = await api.executeSQL({
              sql: sqlResponse.sql,
              database: selectedDatabase,
            });
            newResult.baseline.execution = executeResponse;
          } catch (error) {
            newResult.baseline.error =
              error instanceof Error ? error.message : 'Failed to execute baseline SQL';
          }
        })
        .catch((error) => {
          newResult.baseline.error =
            error instanceof Error ? error.message : 'Failed to generate baseline SQL';
        }),

      // Enhanced SQL generation and execution
      api
        .generateSQLEnhanced(request)
        .then(async (sqlResponse) => {
          newResult.enhanced.sql = sqlResponse;
          // Execute the SQL
          try {
            const executeResponse = await api.executeSQL({
              sql: sqlResponse.sql,
              database: selectedDatabase,
            });
            newResult.enhanced.execution = executeResponse;
          } catch (error) {
            newResult.enhanced.error =
              error instanceof Error ? error.message : 'Failed to execute enhanced SQL';
          }
        })
        .catch((error) => {
          newResult.enhanced.error =
            error instanceof Error ? error.message : 'Failed to generate enhanced SQL';
        }),
    ]);

    setResult(newResult);
    setIsRunning(false);
  };

  const renderSQLResult = (
    title: string,
    subtitle: string,
    sqlResponse?: TextToSQLResponse,
    executeResponse?: ExecuteResponse,
    error?: string
  ) => {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold">{title}</h3>
          <span className="text-sm text-muted-foreground">{subtitle}</span>
        </div>

        {error && !sqlResponse && (
          <Card>
            <CardContent className="pt-6">
              <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md">
                {error}
              </div>
            </CardContent>
          </Card>
        )}

        {sqlResponse && (
          <>
            {/* SQL Query */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  SQL Query
                  {sqlResponse.metadata.has_semantic_layer && (
                    <Badge variant="default" className="bg-green-600">
                      Semantic Layer Used
                    </Badge>
                  )}
                  {sqlResponse.metadata.has_semantic_layer === false && (
                    <Badge variant="secondary">
                      No Semantic Layer
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  {sqlResponse.explanation}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-zinc-900 text-zinc-100 p-4 rounded-md font-mono text-sm overflow-x-auto">
                  {sqlResponse.sql}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">
                    {sqlResponse.metadata.model}
                  </Badge>
                  <Badge variant="secondary">
                    {sqlResponse.metadata.tokens_used} tokens
                  </Badge>
                  <Badge variant="secondary">
                    ${sqlResponse.metadata.cost_usd.toFixed(6)}
                  </Badge>
                  <Badge variant="secondary">
                    {sqlResponse.metadata.generation_time_ms}ms
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Execution Results or Error */}
            {error && (
              <Card>
                <CardContent className="pt-6">
                  <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md">
                    {error}
                  </div>
                </CardContent>
              </Card>
            )}

            {executeResponse && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Results</CardTitle>
                  <CardDescription>
                    {executeResponse.row_count} rows returned in {executeResponse.execution_time_ms}ms
                    {executeResponse.truncated && ' (truncated to 1000 rows)'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="rounded-md border overflow-hidden">
                    <div className="overflow-x-auto max-h-96 overflow-y-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            {executeResponse.columns.map((col) => (
                              <TableHead key={col} className="sticky top-0 bg-background">
                                {col}
                              </TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {executeResponse.results.map((row, idx) => (
                            <TableRow key={idx}>
                              {executeResponse.columns.map((col) => (
                                <TableCell key={col}>
                                  {row[col] !== null && row[col] !== undefined
                                    ? String(row[col])
                                    : <span className="text-muted-foreground">null</span>}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    );
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-800">
      <div className="container mx-auto px-4 py-8 max-w-[1920px]">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">DataPrism</h1>
            <p className="text-lg text-muted-foreground">
              Natural Language to SQL - Comparison Mode
            </p>
          </div>
          <div className="flex gap-2">
            <a
              href="/admin/semantic"
              className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-md font-medium transition-colors"
            >
              Semantic Layer Admin
            </a>
          </div>
        </div>

        {/* Navigation */}
        <QueryNavigation />

        {/* Main Content */}
        <div className="space-y-6">
          {/* Input Section */}
          <Card>
            <CardHeader>
              <CardTitle>Ask a Question</CardTitle>
              <CardDescription>
                Select a database and ask a question. We'll generate and execute SQL using both baseline (schema only) and enhanced (schema + semantic layer) approaches.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Database Selector */}
              <div>
                <label className="text-sm font-medium mb-2 block">Database</label>
                <Select
                  value={selectedDatabase}
                  onValueChange={handleDatabaseChange}
                  disabled={isLoadingDatabases}
                >
                  <SelectTrigger>
                    <SelectValue
                      placeholder={isLoadingDatabases ? "Loading databases..." : "Select a database"}
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {databases.map((db) => (
                      <SelectItem key={db} value={db}>
                        {db}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Question Input */}
              <div>
                <label className="text-sm font-medium mb-2 block">Question</label>
                <Textarea
                  placeholder="e.g., What are the top 5 countries by population?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  rows={3}
                />
              </div>

              {/* Run Button */}
              <Button
                onClick={handleRun}
                disabled={isRunning || !selectedDatabase || !question.trim()}
                className="w-full"
                size="lg"
              >
                {isRunning ? 'Running Both Approaches...' : 'Run Comparison'}
              </Button>

              {/* Error Display */}
              {error && (
                <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Comparison Results */}
          {result && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Baseline Results */}
              <div>
                {renderSQLResult(
                  'Baseline',
                  'GPT-4o-mini, schema only',
                  result.baseline.sql,
                  result.baseline.execution,
                  result.baseline.error
                )}
              </div>

              {/* Enhanced Results */}
              <div>
                {renderSQLResult(
                  'Enhanced',
                  'GPT-4o, schema + semantic layer',
                  result.enhanced.sql,
                  result.enhanced.execution,
                  result.enhanced.error
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
