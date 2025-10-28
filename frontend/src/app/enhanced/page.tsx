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

export default function EnhancedPage() {
  // State
  const [databases, setDatabases] = useState<string[]>([]);
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [sqlResponse, setSqlResponse] = useState<TextToSQLResponse | null>(null);
  const [executeResponse, setExecuteResponse] = useState<ExecuteResponse | null>(null);
  const [isLoadingDatabases, setIsLoadingDatabases] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
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
    // Reset interface when database changes
    setQuestion('');
    setSqlResponse(null);
    setExecuteResponse(null);
    setError('');
  };

  const handleGenerateSQL = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }
    if (!selectedDatabase) {
      setError('Please select a database');
      return;
    }

    setError('');
    setIsGenerating(true);
    setSqlResponse(null);
    setExecuteResponse(null);

    try {
      const response = await api.generateSQLEnhanced({
        question: question.trim(),
        database: selectedDatabase,
      });
      setSqlResponse(response);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to generate SQL');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExecuteSQL = async () => {
    if (!sqlResponse?.sql) {
      setError('No SQL to execute');
      return;
    }
    if (!selectedDatabase) {
      setError('Please select a database');
      return;
    }

    setError('');
    setIsExecuting(true);
    setExecuteResponse(null);

    try {
      const response = await api.executeSQL({
        sql: sqlResponse.sql,
        database: selectedDatabase,
      });
      setExecuteResponse(response);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to execute SQL');
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-800">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">QueryDawg</h1>
            <p className="text-lg text-muted-foreground">
              Natural Language to SQL - Enhanced Mode
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
        <div className="grid gap-6">
          {/* Input Section */}
          <Card>
            <CardHeader>
              <CardTitle>Ask a Question</CardTitle>
              <CardDescription>
                Select a database and ask a question in natural language. Uses schema + semantic layer (GPT-4o-mini).
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

              {/* Generate Button */}
              <Button
                onClick={handleGenerateSQL}
                disabled={isGenerating || !selectedDatabase || !question.trim()}
                className="w-full"
              >
                {isGenerating ? 'Generating...' : 'Generate SQL'}
              </Button>

              {/* Error Display */}
              {error && (
                <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>

          {/* SQL Output */}
          {sqlResponse && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  Generated SQL
                  {sqlResponse.metadata.has_semantic_layer && (
                    <Badge variant="default" className="bg-green-600">
                      Semantic Layer Used
                    </Badge>
                  )}
                  {!sqlResponse.metadata.has_semantic_layer && (
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
                {/* SQL Code */}
                <div className="bg-zinc-900 text-zinc-100 p-4 rounded-md font-mono text-sm overflow-x-auto">
                  {sqlResponse.sql}
                </div>

                {/* Metadata */}
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

                {/* Execute Button */}
                <Button
                  onClick={handleExecuteSQL}
                  disabled={isExecuting}
                  className="w-full"
                  variant="default"
                >
                  {isExecuting ? 'Executing...' : 'Execute SQL'}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Results */}
          {executeResponse && (
            <Card>
              <CardHeader>
                <CardTitle>Results</CardTitle>
                <CardDescription>
                  {executeResponse.row_count} rows returned in {executeResponse.execution_time_ms}ms
                  {executeResponse.truncated && ' (truncated to 1000 rows)'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border overflow-hidden">
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {executeResponse.columns.map((col) => (
                            <TableHead key={col}>{col}</TableHead>
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
        </div>
      </div>
    </main>
  );
}
