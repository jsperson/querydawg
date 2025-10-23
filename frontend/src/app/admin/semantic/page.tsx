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

interface DatabaseStatus {
  name: string;
  hasLayer: boolean;
  layerInfo?: SemanticLayerListItem;
  isGenerating: boolean;
  lastResult?: SemanticLayerResponse | Error;
}

export default function SemanticLayerAdmin() {
  const [databases, setDatabases] = useState<DatabaseStatus[]>([]);
  const [selectedDatabases, setSelectedDatabases] = useState<Set<string>>(new Set());
  const [customInstructions, setCustomInstructions] = useState<string>('');
  const [anonymize, setAnonymize] = useState<boolean>(true);
  const [sampleRows, setSampleRows] = useState<number>(10);
  const [promptResponse, setPromptResponse] = useState<ViewPromptResponse | null>(null);
  const [isLoadingDatabases, setIsLoadingDatabases] = useState(true);
  const [isViewingPrompt, setIsViewingPrompt] = useState(false);
  const [error, setError] = useState<string>('');
  const connectionName = 'Supabase';

  useEffect(() => {
    loadDatabases();
    loadCustomInstructions();
  }, []);

  const loadDatabases = async () => {
    try {
      setIsLoadingDatabases(true);
      const [dbResponse, layers] = await Promise.all([
        api.getDatabases(),
        api.listSemanticLayers(),
      ]);

      const layerMap = new Map(layers.map(l => [l.database_name, l]));

      const statusList: DatabaseStatus[] = dbResponse.databases.map(name => ({
        name,
        hasLayer: layerMap.has(name),
        layerInfo: layerMap.get(name),
        isGenerating: false,
      }));

      setDatabases(statusList);
      setError('');
    } catch {
      setError('Failed to load databases');
    } finally {
      setIsLoadingDatabases(false);
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
      setSelectedDatabases(new Set(databases.map(d => d.name)));
    }
  };

  const handleViewPrompt = async () => {
    if (selectedDatabases.size === 0) {
      setError('Please select at least one database');
      return;
    }

    const firstDatabase = Array.from(selectedDatabases)[0];
    setError('');
    setIsViewingPrompt(true);
    setPromptResponse(null);

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

    // Check for existing layers
    const existingLayers = Array.from(selectedDatabases).filter(db =>
      databases.find(d => d.name === db)?.hasLayer
    );

    if (existingLayers.length > 0) {
      const message = existingLayers.length === 1
        ? `${existingLayers[0]} already has a semantic layer. Generating will replace it.`
        : `The following databases already have semantic layers:\n${existingLayers.join(', ')}\n\nGenerating will replace them.`;

      if (!window.confirm(`${message}\n\nDo you want to continue?`)) {
        return;
      }
    }

    setError('');
    setPromptResponse(null);

    // Mark selected databases as generating
    setDatabases(prev => prev.map(d => ({
      ...d,
      isGenerating: selectedDatabases.has(d.name),
      lastResult: selectedDatabases.has(d.name) ? undefined : d.lastResult,
    })));

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

        // Update this database's status
        setDatabases(prev => prev.map(d =>
          d.name === database
            ? { ...d, isGenerating: false, hasLayer: true, lastResult: response }
            : d
        ));
      } catch (error) {
        const err = error instanceof Error ? error : new Error('Unknown error');
        setDatabases(prev => prev.map(d =>
          d.name === database
            ? { ...d, isGenerating: false, lastResult: err }
            : d
        ));
      }
    }

    // Reload to get updated layer info
    await loadDatabases();
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

  const handleDelete = async (database: string) => {
    setError('');

    try {
      await api.deleteSemanticLayer(database, connectionName);

      // Force reload from server to get fresh state
      await loadDatabases();
    } catch (error) {
      console.error('Delete error:', error);
      const errorMsg = error instanceof Error ? error.message : 'Failed to delete';
      setError(errorMsg);

      // Reload to restore correct state
      await loadDatabases();
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedDatabases.size === 0) return;

    setError('');

    // Get databases with layers from selected set
    const toDelete = Array.from(selectedDatabases).filter(db =>
      databases.find(d => d.name === db)?.hasLayer
    );

    // Delete sequentially (silently skip if no layers to delete)
    for (const database of toDelete) {
      try {
        await api.deleteSemanticLayer(database, connectionName);
      } catch (error) {
        console.error(`Delete error for ${database}:`, error);
      }
    }

    // Reload all databases to get fresh state
    await loadDatabases();
  };

  const handleGenerateSingle = async (database: string) => {
    setError('');
    setPromptResponse(null);

    // Mark this database as generating
    setDatabases(prev => prev.map(d => ({
      ...d,
      isGenerating: d.name === database,
      lastResult: d.name === database ? undefined : d.lastResult,
    })));

    try {
      const response = await api.generateSemanticLayer({
        database,
        custom_instructions: customInstructions || undefined,
        anonymize,
        sample_rows: sampleRows,
        connection_name: connectionName,
      });

      // Update this database's status
      setDatabases(prev => prev.map(d =>
        d.name === database
          ? { ...d, isGenerating: false, hasLayer: true, lastResult: response }
          : d
      ));
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Unknown error');
      setDatabases(prev => prev.map(d =>
        d.name === database
          ? { ...d, isGenerating: false, lastResult: err }
          : d
      ));
    }

    // Reload to get updated layer info
    await loadDatabases();
  };

  const generatingCount = databases.filter(d => d.isGenerating).length;

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-800">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="mb-4 flex items-center justify-between">
            <a
              href="/"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              ← Back to Query Interface
            </a>
            <a
              href="/admin/semantic/view"
              className="text-sm text-primary hover:text-primary/80 transition-colors"
            >
              View Semantic Layers →
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
              <CardTitle>Generation Options</CardTitle>
              <CardDescription>
                Configure settings for semantic layer generation
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
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
            </CardContent>
          </Card>

          {/* Databases Section */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Databases ({selectedDatabases.size} selected)</CardTitle>
                  <CardDescription>
                    Select databases to generate semantic layers
                  </CardDescription>
                </div>
                <Button
                  onClick={toggleSelectAll}
                  variant="outline"
                  size="sm"
                  disabled={isLoadingDatabases}
                >
                  {selectedDatabases.size === databases.length ? 'Deselect All' : 'Select All'}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingDatabases ? (
                <div className="text-sm text-muted-foreground">Loading databases...</div>
              ) : (
                <div className="space-y-2">
                  {databases.map((db) => (
                    <div
                      key={db.name}
                      className="flex items-center gap-3 p-3 border rounded-md hover:bg-zinc-50 dark:hover:bg-zinc-800"
                    >
                      <Checkbox
                        checked={selectedDatabases.has(db.name)}
                        onCheckedChange={() => toggleDatabase(db.name)}
                        disabled={db.isGenerating}
                      />
                      <span className="flex-1 font-mono text-sm font-medium">{db.name}</span>

                      {/* Status Badge */}
                      {db.isGenerating ? (
                        <Badge variant="secondary" className="text-xs">
                          Generating...
                        </Badge>
                      ) : db.hasLayer ? (
                        <Badge variant="default" className="text-xs">
                          Has Layer
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-xs">
                          No Layer
                        </Badge>
                      )}

                      {/* Result Badge */}
                      {db.lastResult && (
                        <Badge
                          variant={db.lastResult instanceof Error ? "destructive" : "default"}
                          className="text-xs"
                        >
                          {db.lastResult instanceof Error ? "Failed" : "Success"}
                        </Badge>
                      )}

                      {/* Action Buttons */}
                      {!db.isGenerating && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleGenerateSingle(db.name)}
                            disabled={db.isGenerating}
                          >
                            Generate
                          </Button>
                          {db.hasLayer && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => window.location.href = `/admin/semantic/view?db=${db.name}`}
                              >
                                View
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleDelete(db.name)}
                              >
                                Delete
                              </Button>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Action Buttons */}
              <div className="grid grid-cols-3 gap-2 mt-4">
                <Button
                  onClick={handleViewPrompt}
                  disabled={isViewingPrompt || selectedDatabases.size === 0}
                  variant="outline"
                >
                  {isViewingPrompt ? 'Loading Prompt...' : 'View Prompt'}
                </Button>
                <Button
                  onClick={handleGenerate}
                  disabled={generatingCount > 0 || selectedDatabases.size === 0}
                >
                  {generatingCount > 0
                    ? `Generating (${generatingCount}/${selectedDatabases.size})...`
                    : `Generate Selected`}
                </Button>
                <Button
                  onClick={handleDeleteSelected}
                  disabled={generatingCount > 0 || selectedDatabases.size === 0}
                  variant="destructive"
                >
                  Delete Selected
                </Button>
              </div>

              {/* Error Display */}
              {error && (
                <div className="mt-4 bg-destructive/10 text-destructive px-4 py-3 rounded-md">
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
        </div>
      </div>
    </main>
  );
}
