import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { FileText } from 'lucide-react'

export interface PromptNodeData {
  prompt: string
}

export const PromptNode = memo(({ data }: { data: PromptNodeData }) => {
  return (
    <div className="bg-card border-2 border-border rounded-lg p-4 w-[320px] shadow-lg">
      <div className="flex items-center gap-2 mb-2">
        <FileText className="h-5 w-5 text-primary" />
        <div className="font-semibold">Base Prompt</div>
      </div>
      <div className="text-sm text-muted-foreground line-clamp-3">
        {data.prompt as string}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-primary" />
    </div>
  )
})

PromptNode.displayName = 'PromptNode'
