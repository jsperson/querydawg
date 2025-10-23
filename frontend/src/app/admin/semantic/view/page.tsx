'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type {
  SemanticLayerResponse,
  SemanticLayerListItem,
} from '@/lib/api-types';

export default function ViewSemanticLayer() {
  const [semanticLayers, setSemanticLayers] = useState<SemanticLayerListItem[]>([]);
  const [selectedLayer, setSelectedLayer] = useState<SemanticLayerResponse | null>(null);
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingLayer, setIsLoadingLayer] = useState(false);
  const [error, setError] = useState<string>('');
  const connectionName = 'Supabase';

  useEffect(() => {
    loadSemanticLayers();
  }, []);

  const loadSemanticLayers = async () => {
    try {
      setIsLoading(true);
      const layers = await api.listSemanticLayers();
      setSemanticLayers(layers);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load semantic layers');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectDatabase = async (database: string) => {
    setSelectedDatabase(database);
    setIsLoadingLayer(true);
    setError('');

    try {
      const layer = await api.getSemanticLayer(database);
      setSelectedLayer(layer);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load semantic layer');
      setSelectedLayer(null);
    } finally {
      setIsLoadingLayer(false);
    }
  };

  const renderSemanticLayer = (layer: any) => {
    return (
      <div className="space-y-4">
        {layer.tables?.map((table: any, idx: number) => (
          <Card key={idx}>
            <CardHeader>
              <CardTitle className="text-lg font-mono">{table.name}</CardTitle>
              <CardDescription>{table.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Columns */}
              {table.columns && table.columns.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Columns</h4>
                  <div className="space-y-2">
                    {table.columns.map((col: any, colIdx: number) => (
                      <div
                        key={colIdx}
                        className="border-l-2 border-primary/20 pl-3 py-1"
                      >
                        <div className="flex items-center gap-2">
                          <code className="font-mono text-sm font-semibold">{col.name}</code>
                          <Badge variant="outline" className="text-xs">
                            {col.type}
                          </Badge>
                          {col.primary_key && (
                            <Badge variant="default" className="text-xs">
                              PK
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {col.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Foreign Keys */}
              {table.foreign_keys && table.foreign_keys.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Foreign Keys</h4>
                  <div className="space-y-1">
                    {table.foreign_keys.map((fk: any, fkIdx: number) => (
                      <div key={fkIdx} className="text-sm">
                        <code className="font-mono">{fk.column}</code>
                        {' → '}
                        <code className="font-mono">
                          {fk.referenced_table}.{fk.referenced_column}
                        </code>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sample Values */}
              {table.sample_values && Object.keys(table.sample_values).length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Sample Values</h4>
                  <div className="bg-muted p-3 rounded-md space-y-1 max-h-40 overflow-y-auto">
                    {Object.entries(table.sample_values).map(([column, values]: [string, any]) => (
                      <div key={column} className="text-sm">
                        <span className="font-mono font-semibold">{column}:</span>{' '}
                        <span className="text-muted-foreground">
                          {Array.isArray(values) ? values.join(', ') : String(values)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-800">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="mb-4">
            <a
              href="/admin/semantic"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              ← Back to Semantic Layer Admin
            </a>
          </div>
          <h1 className="text-4xl font-bold mb-2">View Semantic Layers</h1>
          <p className="text-lg text-muted-foreground">
            Browse and inspect generated semantic layer documentation
          </p>
        </div>

        {/* Main Content */}
        <div className="grid gap-6">
          {/* Database Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Select Database</CardTitle>
              <CardDescription>
                Choose a database to view its semantic layer
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="text-sm text-muted-foreground">Loading semantic layers...</div>
              ) : semanticLayers.length === 0 ? (
                <div className="text-sm text-muted-foreground">
                  No semantic layers found. Generate some from the{' '}
                  <a href="/admin/semantic" className="text-primary hover:underline">
                    admin page
                  </a>
                  .
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                  {semanticLayers.map((layer) => (
                    <Button
                      key={layer.id}
                      onClick={() => handleSelectDatabase(layer.database_name)}
                      variant={selectedDatabase === layer.database_name ? 'default' : 'outline'}
                      className="justify-start font-mono text-sm"
                    >
                      {layer.database_name}
                    </Button>
                  ))}
                </div>
              )}

              {error && (
                <div className="mt-4 bg-destructive/10 text-destructive px-4 py-3 rounded-md">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Semantic Layer Display */}
          {isLoadingLayer && (
            <Card>
              <CardContent className="py-8">
                <div className="text-center text-muted-foreground">
                  Loading semantic layer...
                </div>
              </CardContent>
            </Card>
          )}

          {selectedLayer && !isLoadingLayer && (
            <>
              {/* Metadata */}
              <Card>
                <CardHeader>
                  <CardTitle>Metadata</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-semibold">Database:</span>{' '}
                      <code className="font-mono">{selectedLayer.database}</code>
                    </div>
                    <div>
                      <span className="font-semibold">LLM Model:</span>{' '}
                      {selectedLayer.metadata.llm_model}
                    </div>
                    <div>
                      <span className="font-semibold">Generated:</span>{' '}
                      {new Date(selectedLayer.metadata.generated_at).toLocaleString()}
                    </div>
                    <div>
                      <span className="font-semibold">Anonymized:</span>{' '}
                      {selectedLayer.metadata.anonymized ? 'Yes' : 'No'}
                    </div>
                    <div>
                      <span className="font-semibold">Sample Rows:</span>{' '}
                      {selectedLayer.metadata.sample_rows_per_table}
                    </div>
                    <div>
                      <span className="font-semibold">Version:</span>{' '}
                      {selectedLayer.metadata.generator_version}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Semantic Layer Content */}
              <div>
                <h2 className="text-2xl font-bold mb-4">Tables</h2>
                {renderSemanticLayer(selectedLayer.semantic_layer)}
              </div>

              {/* Raw JSON */}
              <Card>
                <CardHeader>
                  <CardTitle>Raw JSON</CardTitle>
                  <CardDescription>
                    Complete semantic layer data structure
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <pre className="bg-zinc-900 text-zinc-100 p-4 rounded-md overflow-x-auto max-h-96 overflow-y-auto text-xs font-mono">
                    {JSON.stringify(selectedLayer.semantic_layer, null, 2)}
                  </pre>
                </CardContent>
              </Card>

              {/* Prompt Used (if available) */}
              {selectedLayer.prompt_used && (
                <Card>
                  <CardHeader>
                    <CardTitle>Prompt Used</CardTitle>
                    <CardDescription>
                      The prompt that was sent to the LLM for generation
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-zinc-900 text-zinc-100 p-4 rounded-md overflow-x-auto max-h-96 overflow-y-auto text-xs whitespace-pre-wrap">
                      {selectedLayer.prompt_used}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
}
