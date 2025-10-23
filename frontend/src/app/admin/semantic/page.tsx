'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import type {
  SemanticLayerResponse,
  ViewPromptResponse,
  SemanticLayerListItem,
} from '@/lib/api-types';

export default function SemanticLayerAdmin() {
  // State
  const [databases, setDatabases] = useState<string[]>([]);
  const [databasesWithLayers, setDatabasesWithLayers] = useState<Set<string>>(new Set());
  const [selectedDatabases, setSelectedDatabases] = useState<Set<string>>(new Set());
  const [customInstructions, setCustomInstructions] = useState<string>('');
  const [anonymize, setAnonymize] = useState<boolean>(true);
  const [sampleRows, setSampleRows] = useState<number>(10);
  const [promptResponse, setPromptResponse] = useState<ViewPromptResponse | null>(null);
  const [generationResults, setGenerationResults] = useState<Map<string, SemanticLayerResponse | Error>>(new Map());
  const [generatingDatabases, setGeneratingDatabases] = useState<Set<string>>(new Set());
  const [existingLayers, setExistingLayers] = useState<SemanticLayerListItem[]>([]);
  const [isLoadingDatabases, setIsLoadingDatabases] = useState(true);
  const [isViewingPrompt, setIsViewingPrompt] = useState(false);
  const [error, setError] = useState<string>('');
  const connectionName = 'Supabase';

  // Load databases and existing layers on mount
  useEffect(() => {
    loadDatabases();
    loadDatabasesWithLayers();
    loadExistingLayers();
    loadCustomInstructions();
  }, []);

  const loadDatabases = async () => {
    try {
      setIsLoadingDatabases(true);
      const response = await api.getDatabases();
      setDatabases(response.databases);
      setError('');
    } catch {
      setError('Failed to load databases');
    } finally {
      setIsLoadingDatabases(false);
    }
  };

  const loadDatabasesWithLayers = async () => {
    try {
      const response = await api.getDatabasesWithSemanticLayers(connectionName);
      setDatabasesWithLayers(new Set(response.databases));
    } catch {
      // Silently fail - not critical
    }
  };

  const loadExistingLayers = async () => {
    try {
      const layers = await api.listSemanticLayers();
      setExistingLayers(layers);
    } catch {
      // Silently fail - not critical
    }
  };

  const loadCustomInstructions = async () => {
    try {
      const response = await api.getCustomInstructions();
      if (response.instructions) {
        setCustomInstructions(response.instructions);
      }
    } catch {
      // Silently fail - not critical
    }
  };

  const toggleDatabase = (database: string) => {
    const newSelected = new Set(selectedDatabases);
    if (newSelected.has(database)) {
      newSelected.delete(database);
    } else {
      newSelected.add(database);
    }
    setSelectedDatabases(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedDatabases.size === databases.length) {
      setSelectedDatabases(new Set());
    } else {
      setSelectedDatabases(new Set(databases));
    }
  };

  const handleViewPrompt = async () => {
    if (selectedDatabases.size === 0) {
      setError('Please select at least one database');
      return;
    }

    // Use first selected database for prompt preview
    const firstDatabase = Array.from(selectedDatabases)[0];

    setError('');
    setIsViewingPrompt(true);
    setPromptResponse(null);
    setGenerationResults(new Map());

    try {
      const response = await api.viewPrompt({
        database: firstDatabase,
        custom_instructions: customInstructions || undefined,
        anonymize,
        sample_rows: sampleRows,
      });
      setPromptResponse(response);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to get prompt');
    } finally {
      setIsViewingPrompt(false);
    }
  };

  const handleGenerate = async () => {
    if (selectedDatabases.size === 0) {
      setError('Please select at least one database');
      return;
    }

    setError('');
    setPromptResponse(null);
    setGenerationResults(new Map());
    setGeneratingDatabases(new Set(selectedDatabases));

    const results = new Map<string, SemanticLayerResponse | Error>();

    // Generate for each selected database sequentially
    for (const database of Array.from(selectedDatabases)) {
      try {
        const response = await api.generateSemanticLayer({
          database,
          custom_instructions: customInstructions || undefined,
          anonymize,
          sample_rows: sampleRows,
          connection_name: connectionName,
        });
        results.set(database, response);
      } catch (error) {
        results.set(database, error instanceof Error ? error : new Error('Unknown error'));
      }

      // Update results after each completion
      setGenerationResults(new Map(results));
    }

    setGeneratingDatabases(new Set());

    // Reload status and layers
    await loadDatabasesWithLayers();
    await loadExistingLayers();
  };

  const handleSaveInstructions = async () => {
    try {
      await api.setCustomInstructions({ instructions: customInstructions });
      setError('');
      alert('Custom instructions saved!');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save instructions');
    }
  };

  const hasLayer = (database: string) => databasesWithLayers.has(database);
  const isGenerating = (database: string) => generatingDatabases.has(database);

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-800">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="mb-4">
            <a
              href="/"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              ← Back to Query Interface
            </a>
          </div>
          <h1 className="text-4xl font-bold mb-2">Semantic Layer Admin</h1>
          <p className="text-lg text-muted-foreground">
            Generate and manage semantic layers for databases
          </p>
        </div>

        {/* Main Content */}
        <div className="grid gap-6">
          {/* Configuration Section */}
          <Card>
            <CardHeader>
              <CardTitle>Configuration</CardTitle>
              <CardDescription>
                Select databases and configure generation options
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Database Multi-Select */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="text-sm font-medium">
                    Databases ({selectedDatabases.size} selected)
                  </label>
                  <Button
                    onClick={toggleSelectAll}
                    variant="outline"
                    size="sm"
                    disabled={isLoadingDatabases}
                  >
                    {selectedDatabases.size === databases.length ? 'Deselect All' : 'Select All'}
                  </Button>
                </div>

                {isLoadingDatabases ? (
                  <div className="text-sm text-muted-foreground">Loading databases...</div>
                ) : (
                  <div className="border rounded-md p-3 max-h-64 overflow-y-auto space-y-2">
                    {databases.map((db) => (
                      <label
                        key={db}
                        className="flex items-center space-x-3 p-2 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer"
                      >
                        <Checkbox
                          checked={selectedDatabases.has(db)}
                          onCheckedChange={() => toggleDatabase(db)}
                          disabled={isGenerating(db)}
                        />
                        <span className="flex-1 font-mono text-sm">{db}</span>
                        {isGenerating(db) ? (
                          <Badge variant="secondary" className="text-xs">
                            Generating...
                          </Badge>
                        ) : hasLayer(db) ? (
                          <Badge variant="default" className="text-xs">
                            ✓ Has Layer
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs">
                            No Layer
                          </Badge>
                        )}
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Options */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Sample Rows</label>
                  <input
                    type="number"
                    value={sampleRows}
                    onChange={(e) => setSampleRows(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md"
                    min="1"
                    max="100"
                  />
                </div>
                <div className="flex items-end">
                  <label className="flex items-center space-x-2">
                    <Checkbox
                      checked={anonymize}
                      onCheckedChange={(checked) => setAnonymize(checked as boolean)}
                    />
                    <span className="text-sm font-medium">Anonymize database name</span>
                  </label>
                </div>
              </div>

              {/* Custom Instructions */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Custom Instructions (Optional)
                </label>
                <Textarea
                  placeholder="Additional instructions for semantic layer generation..."
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                  rows={4}
                />
                <Button
                  onClick={handleSaveInstructions}
                  variant="outline"
                  size="sm"
                  className="mt-2"
                >
                  Save as Default Instructions
                </Button>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button
                  onClick={handleViewPrompt}
                  disabled={isViewingPrompt || selectedDatabases.size === 0}
                  variant="outline"
                  className="flex-1"
                >
                  {isViewingPrompt ? 'Loading Prompt...' : 'View Prompt'}
                </Button>
                <Button
                  onClick={handleGenerate}
                  disabled={generatingDatabases.size > 0 || selectedDatabases.size === 0}
                  className="flex-1"
                >
                  {generatingDatabases.size > 0
                    ? `Generating (${generatingDatabases.size}/${selectedDatabases.size})...`
                    : `Generate for ${selectedDatabases.size} Database(s)`}
                </Button>
              </div>

              {/* Error Display */}
              {error && (
                <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Generation Results */}
          {generationResults.size > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Generation Results</CardTitle>
                <CardDescription>
                  {generationResults.size} database(s) processed
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Array.from(generationResults.entries()).map(([database, result]) => (
                    <div
                      key={database}
                      className="border rounded-md p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono font-medium">{database}</span>
                        {result instanceof Error ? (
                          <Badge variant="destructive">Failed</Badge>
                        ) : (
                          <Badge variant="default">Success</Badge>
                        )}
                      </div>
                      {result instanceof Error ? (
                        <div className="text-sm text-destructive">{result.message}</div>
                      ) : (
                        <div className="text-sm text-muted-foreground">
                          Generated using {result.metadata.llm_model}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Prompt Output */}
          {promptResponse && (
            <Card>
              <CardHeader>
                <CardTitle>Prompt Preview</CardTitle>
                <CardDescription>
                  Prompt that will be sent to LLM (Length: {promptResponse.prompt_length} chars)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-zinc-900 text-zinc-100 p-4 rounded-md font-mono text-xs overflow-x-auto max-h-96 overflow-y-auto whitespace-pre-wrap">
                  {promptResponse.prompt}
                </div>
                <div className="mt-4">
                  <Badge variant={promptResponse.anonymized === 'True' ? 'default' : 'secondary'}>
                    {promptResponse.anonymized === 'True' ? 'Anonymized' : 'Not Anonymized'}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Existing Layers */}
          {existingLayers.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Existing Semantic Layers</CardTitle>
                <CardDescription>
                  {existingLayers.length} layer(s) stored
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {existingLayers.map((layer) => (
                    <div
                      key={layer.id}
                      className="flex items-center justify-between p-3 border rounded-md"
                    >
                      <div>
                        <div className="font-medium font-mono">{layer.database_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {layer.llm_model} • {new Date(layer.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Badge variant="outline">{layer.connection_name}</Badge>
                        <Badge variant="outline">{layer.version}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </main>
  );
}
