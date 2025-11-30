import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { Users } from 'lucide-react'

export interface TargetGroupNodeData extends Record<string, unknown> {
  name: string
}

export const TargetGroupNode = memo(({ data }: { data: TargetGroupNodeData }) => {
  return (
    <div className="bg-card border-2 border-border rounded-lg p-4 w-[280px] shadow-lg">
      <Handle type="target" position={Position.Top} className="!bg-primary" />
      <div className="flex items-center gap-2">
        <Users className="h-5 w-5 text-primary" />
        <div className="font-semibold">{data.name as string}</div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-primary" />
    </div>
  )
})

TargetGroupNode.displayName = 'TargetGroupNode'
