import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { TrendingUp } from 'lucide-react'

export interface AnalyticsNodeData extends Record<string, unknown> {
  winnerCount: number
  improvements: {
    clickRate: string
    conversionRate: string
    engagement: string
  }
  differentiationText?: string
  differentiationTags?: string[]
  iterationNumber?: number
}

export const AnalyticsNode = memo(({ data }: { data: AnalyticsNodeData }) => {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 border-2 border-blue-500 rounded-lg p-3 w-[280px] shadow-lg">
      <Handle type="target" position={Position.Top} className="!bg-blue-500" />

      <div className="space-y-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-blue-500/10 p-1 rounded">
              <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="text-sm font-semibold text-blue-900 dark:text-blue-100">
              Analytics
              {data.iterationNumber !== undefined && (
                <span className="ml-1 text-xs font-normal text-blue-600 dark:text-blue-400">
                  (Iter {data.iterationNumber as number})
                </span>
              )}
            </div>
          </div>
          <div className="bg-blue-500 text-white text-xs font-semibold px-2 py-0.5 rounded">
            {data.winnerCount as number} Winners
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="flex gap-2 text-xs">
          <div className="flex-1 bg-white dark:bg-gray-800 p-1.5 rounded border border-blue-200 dark:border-blue-800 text-center">
            <div className="font-bold text-green-600 dark:text-green-400">
              {(data.improvements as AnalyticsNodeData['improvements']).clickRate}
            </div>
            <div className="text-muted-foreground text-xs">CTR</div>
          </div>
          <div className="flex-1 bg-white dark:bg-gray-800 p-1.5 rounded border border-blue-200 dark:border-blue-800 text-center">
            <div className="font-bold text-green-600 dark:text-green-400">
              {(data.improvements as AnalyticsNodeData['improvements']).conversionRate}
            </div>
            <div className="text-muted-foreground text-xs">CVR</div>
          </div>
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-blue-500" />
    </div>
  )
})

AnalyticsNode.displayName = 'AnalyticsNode'
