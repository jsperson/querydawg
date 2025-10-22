'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [customInstructions, setCustomInstructions] = useState<string>('');
  const [anonymize, setAnonymize] = useState<boolean>(true);
  const [sampleRows, setSampleRows] = useState<number>(10);
  const [promptResponse, setPromptResponse] = useState<ViewPromptResponse | null>(null);
  const [semanticLayerResponse, setSemanticLayerResponse] = useState<SemanticLayerResponse | null>(null);
  const [existingLayers, setExistingLayers] = useState<SemanticLayerListItem[]>([]);
  const [isLoadingDatabases, setIsLoadingDatabases] = useState(true);
  const [isViewingPrompt, setIsViewingPrompt] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingLayers, setIsLoadingLayers] = useState(false);
  const [error, setError] = useState<string>('');

  // Load databases and existing layers on mount
  useEffect(() => {
    loadDatabases();
    loadExistingLayers();
    loadCustomInstructions();
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

  const loadExistingLayers = async () => {
    try {
      setIsLoadingLayers(true);
      const layers = await api.listSemanticLayers();
      setExistingLayers(layers);
    } catch {
      // Silently fail - not critical
    } finally {
      setIsLoadingLayers(false);
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

  const handleViewPrompt = async () => {
    if (!selectedDatabase) {
      setError('Please select a database');
      return;
    }

    setError('');
    setIsViewingPrompt(true);
    setPromptResponse(null);
    setSemanticLayerResponse(null);

    try {
      const response = await api.viewPrompt({
        database: selectedDatabase,
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
    if (!selectedDatabase) {
      setError('Please select a database');
      return;
    }

    setError('');
    setIsGenerating(true);
    setPromptResponse(null);
    setSemanticLayerResponse(null);

    try {
      const response = await api.generateSemanticLayer({
        database: selectedDatabase,
        custom_instructions: customInstructions || undefined,
        anonymize,
        sample_rows: sampleRows,
      });
      setSemanticLayerResponse(response);
      // Reload existing layers
      await loadExistingLayers();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to generate semantic layer');
    } finally {
      setIsGenerating(false);
    }
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

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-800">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
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
                Select database and configure generation options
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Database Selector */}
              <div>
                <label className="text-sm font-medium mb-2 block">Database</label>
                <Select
                  value={selectedDatabase}
                  onValueChange={setSelectedDatabase}
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
                  disabled={isViewingPrompt || !selectedDatabase}
                  variant="outline"
                  className="flex-1"
                >
                  {isViewingPrompt ? 'Loading Prompt...' : 'View Prompt'}
                </Button>
                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating || !selectedDatabase}
                  className="flex-1"
                >
                  {isGenerating ? 'Generating...' : 'Generate Semantic Layer'}
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

          {/* Semantic Layer Output */}
          {semanticLayerResponse && (
            <Card>
              <CardHeader>
                <CardTitle>Generated Semantic Layer</CardTitle>
                <CardDescription>
                  Database: {semanticLayerResponse.database}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Metadata */}
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">
                    {semanticLayerResponse.metadata.llm_model}
                  </Badge>
                  <Badge variant="secondary">
                    {semanticLayerResponse.metadata.llm_provider}
                  </Badge>
                  <Badge variant="secondary">
                    {semanticLayerResponse.metadata.sample_rows_per_table} sample rows
                  </Badge>
                  <Badge variant={semanticLayerResponse.metadata.anonymized ? 'default' : 'secondary'}>
                    {semanticLayerResponse.metadata.anonymized ? 'Anonymized' : 'Not Anonymized'}
                  </Badge>
                </div>

                {/* Semantic Layer JSON */}
                <div>
                  <div className="bg-zinc-900 text-zinc-100 p-4 rounded-md font-mono text-xs overflow-x-auto max-h-96 overflow-y-auto">
                    {JSON.stringify(semanticLayerResponse.semantic_layer, null, 2)}
                  </div>
                </div>

                {/* Prompt Used (if available) */}
                {semanticLayerResponse.prompt_used && (
                  <details>
                    <summary className="cursor-pointer font-medium">View Prompt Used</summary>
                    <div className="mt-2 bg-zinc-900 text-zinc-100 p-4 rounded-md font-mono text-xs overflow-x-auto max-h-96 overflow-y-auto whitespace-pre-wrap">
                      {semanticLayerResponse.prompt_used}
                    </div>
                  </details>
                )}
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
                        <div className="font-medium">{layer.database_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {layer.llm_model} • {new Date(layer.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex gap-2">
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
