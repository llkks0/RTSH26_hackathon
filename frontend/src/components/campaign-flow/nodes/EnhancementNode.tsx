import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { Sparkles } from 'lucide-react'

export interface EnhancementNodeData extends Record<string, unknown> {
  prompt: string
  title?: string
  notes?: string
  usedAssets?: string[]
}

export const EnhancementNode = memo(({ data }: { data: EnhancementNodeData }) => {
  return (
    <div className="bg-card border-2 border-primary/50 rounded-lg p-4 w-[320px] shadow-lg">
      <Handle type="target" position={Position.Top} className="!bg-primary" />
      <div className="flex items-center gap-2 mb-2">
        <div className="bg-primary/10 p-1.5 rounded">
          <Sparkles className="h-4 w-4 text-primary" />
        </div>
        <div className="font-semibold">{(data.title as string) || 'AI Enhanced Prompt'}</div>
      </div>
      <div className="text-sm text-muted-foreground line-clamp-3">
        {data.prompt as string}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-primary" />
    </div>
  )
})

EnhancementNode.displayName = 'EnhancementNode'
