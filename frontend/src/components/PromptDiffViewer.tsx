"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Copy, Check } from "lucide-react"

interface SemanticChunk {
  chunk_type: string
  table_name?: string
  score: number
  text: string
}

interface PromptDiffViewerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  baselineSystemPrompt?: string | null
  baselineUserPrompt?: string | null
  enhancedSystemPrompt?: string | null
  enhancedUserPrompt?: string | null
  enhancedSemanticChunks?: string | null
  questionId: string
  database: string
}

export function PromptDiffViewer({
  open,
  onOpenChange,
  baselineSystemPrompt,
  baselineUserPrompt,
  enhancedSystemPrompt,
  enhancedUserPrompt,
  enhancedSemanticChunks,
  questionId,
  database,
}: PromptDiffViewerProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null)

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const getDiffLines = (baseline: string, enhanced: string) => {
    const baselineLines = baseline.split('\n')
    const enhancedLines = enhanced.split('\n')

    const maxLines = Math.max(baselineLines.length, enhancedLines.length)
    const result: Array<{
      baselineLine: string
      enhancedLine: string
      isDifferent: boolean
      lineNumber: number
    }> = []

    for (let i = 0; i < maxLines; i++) {
      const baseLine = baselineLines[i] || ''
      const enhLine = enhancedLines[i] || ''
      result.push({
        baselineLine: baseLine,
        enhancedLine: enhLine,
        isDifferent: baseLine !== enhLine,
        lineNumber: i + 1
      })
    }

    return result
  }

  const renderDiffView = (baseline: string, enhanced: string, title: string) => {
    if (!baseline && !enhanced) {
      return <div className="text-muted-foreground p-4">No prompts available</div>
    }

    const diffLines = getDiffLines(baseline || '', enhanced || '')
    const hasChanges = diffLines.some(l => l.isDifferent)

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold">{title}</h3>
            {hasChanges && (
              <Badge variant="outline" className="bg-yellow-50">
                {diffLines.filter(l => l.isDifferent).length} lines different
              </Badge>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Baseline */}
          <div className="border rounded-lg">
            <div className="bg-muted px-3 py-2 border-b flex items-center justify-between">
              <span className="text-sm font-medium">Baseline</span>
              {baseline && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(baseline, `baseline-${title}`)}
                >
                  {copiedField === `baseline-${title}` ? (
                    <Check className="h-3 w-3" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </Button>
              )}
            </div>
            <ScrollArea className="h-[600px]">
              <div className="p-3 font-mono text-xs">
                {diffLines.map((line, idx) => (
                  <div
                    key={idx}
                    className={`flex ${line.isDifferent ? 'bg-red-50 dark:bg-red-950/20' : ''}`}
                  >
                    <span className="text-muted-foreground select-none w-12 flex-shrink-0 pr-4 text-right">
                      {line.baselineLine && line.lineNumber}
                    </span>
                    <span className="whitespace-pre-wrap break-all">{line.baselineLine}</span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>

          {/* Enhanced */}
          <div className="border rounded-lg">
            <div className="bg-muted px-3 py-2 border-b flex items-center justify-between">
              <span className="text-sm font-medium">Enhanced (with Semantic Layer)</span>
              {enhanced && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(enhanced, `enhanced-${title}`)}
                >
                  {copiedField === `enhanced-${title}` ? (
                    <Check className="h-3 w-3" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </Button>
              )}
            </div>
            <ScrollArea className="h-[600px]">
              <div className="p-3 font-mono text-xs">
                {diffLines.map((line, idx) => (
                  <div
                    key={idx}
                    className={`flex ${line.isDifferent ? 'bg-green-50 dark:bg-green-950/20' : ''}`}
                  >
                    <span className="text-muted-foreground select-none w-12 flex-shrink-0 pr-4 text-right">
                      {line.enhancedLine && line.lineNumber}
                    </span>
                    <span className="whitespace-pre-wrap break-all">{line.enhancedLine}</span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>
    )
  }

  const renderSemanticChunks = () => {
    if (!enhancedSemanticChunks) {
      return <div className="text-muted-foreground p-4">No semantic chunks retrieved</div>
    }

    try {
      const chunks = JSON.parse(enhancedSemanticChunks) as SemanticChunk[]
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Retrieved Semantic Chunks</h3>
            <Badge>{chunks.length} chunks</Badge>
          </div>
          <ScrollArea className="h-[600px]">
            <div className="space-y-4 pr-4">
              {chunks.map((chunk: SemanticChunk, idx: number) => (
                <div key={idx} className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline">{chunk.chunk_type}</Badge>
                    {chunk.table_name && <Badge variant="secondary">{chunk.table_name}</Badge>}
                    <span className="text-xs text-muted-foreground ml-auto">
                      Score: {chunk.score?.toFixed(3)}
                    </span>
                  </div>
                  <pre className="text-xs whitespace-pre-wrap bg-muted p-3 rounded">
                    {chunk.text}
                  </pre>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      )
    } catch {
      return <div className="text-destructive p-4">Error parsing semantic chunks</div>
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] h-[90vh]">
        <DialogHeader>
          <DialogTitle>Prompt Analysis</DialogTitle>
          <DialogDescription>
            Question ID: {questionId} | Database: {database}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="system" className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="system">System Prompt</TabsTrigger>
            <TabsTrigger value="user">User Prompt</TabsTrigger>
            <TabsTrigger value="chunks">Semantic Chunks</TabsTrigger>
          </TabsList>

          <TabsContent value="system" className="flex-1 mt-4">
            {renderDiffView(
              baselineSystemPrompt || '',
              enhancedSystemPrompt || '',
              'System Prompt'
            )}
          </TabsContent>

          <TabsContent value="user" className="flex-1 mt-4">
            {renderDiffView(
              baselineUserPrompt || '',
              enhancedUserPrompt || '',
              'User Prompt'
            )}
          </TabsContent>

          <TabsContent value="chunks" className="flex-1 mt-4">
            {renderSemanticChunks()}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
