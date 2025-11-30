import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { TrendingUp, TrendingDown } from 'lucide-react'

export interface ImageNodeData extends Record<string, unknown> {
  id: string
  imageUrl: string
  isWinner: boolean
  analytics: {
    clickRate: number
    conversionRate: number
    engagement: number
    impressions: number
  }
}

export const ImageNode = memo(({ data }: { data: ImageNodeData }) => {
  const bgClass = (data.isWinner as boolean)
    ? 'bg-green-50 dark:bg-green-950/30 border-green-500'
    : 'bg-muted/50 border-border opacity-60'

  return (
    <div className={`border-2 rounded-lg p-3 w-[200px] shadow-lg ${bgClass}`}>
      <Handle type="target" position={Position.Top} className="!bg-primary" />

      <div className="rounded-md overflow-hidden mb-2 bg-background w-full h-32">
        <img
          src={data.imageUrl as string}
          alt="Generated"
          className="w-full h-full object-cover"
        />
      </div>

      <div className="space-y-1">
        <div className="flex items-center gap-1 justify-between">
          <span className="text-xs font-medium">
            {(data.isWinner as boolean) ? 'Winner' : 'Variant'}
          </span>
          {(data.isWinner as boolean) ? (
            <TrendingUp className="h-3 w-3 text-green-600 dark:text-green-400" />
          ) : (
            <TrendingDown className="h-3 w-3 text-muted-foreground" />
          )}
        </div>

        <div className="text-xs space-y-0.5 text-muted-foreground">
          <div>CTR: {(data.analytics as ImageNodeData['analytics']).clickRate.toFixed(2)}%</div>
          <div>CVR: {(data.analytics as ImageNodeData['analytics']).conversionRate.toFixed(2)}%</div>
          <div>Eng: {(data.analytics as ImageNodeData['analytics']).engagement.toFixed(2)}%</div>
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-primary" />
    </div>
  )
})

ImageNode.displayName = 'ImageNode'
