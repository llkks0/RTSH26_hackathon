import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { TrendingUp, Loader2 } from 'lucide-react'
import type { StepState } from '@/lib/mockFlowData'

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
  stepState?: StepState
}

export const AnalyticsNode = memo(({ data }: { data: AnalyticsNodeData }) => {
  const isAnalyzing = data.stepState === 'analyzing'

  const containerClass = isAnalyzing
    ? 'bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800/50 dark:to-gray-900/50 border-2 border-gray-400 dark:border-gray-600 rounded-lg p-3 w-[280px] shadow-lg animate-pulse'
    : 'bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 border-2 border-blue-500 rounded-lg p-3 w-[280px] shadow-lg'

  const iconBgClass = isAnalyzing ? 'bg-gray-400/10' : 'bg-blue-500/10'
  const iconClass = isAnalyzing ? 'h-4 w-4 text-gray-500 dark:text-gray-400' : 'h-4 w-4 text-blue-600 dark:text-blue-400'
  const titleClass = isAnalyzing ? 'text-sm font-semibold text-gray-700 dark:text-gray-300' : 'text-sm font-semibold text-blue-900 dark:text-blue-100'
  const subtitleClass = isAnalyzing ? 'text-xs font-normal text-gray-500 dark:text-gray-400' : 'text-xs font-normal text-blue-600 dark:text-blue-400'
  const badgeClass = isAnalyzing ? 'bg-gray-400 text-white text-xs font-semibold px-2 py-0.5 rounded' : 'bg-blue-500 text-white text-xs font-semibold px-2 py-0.5 rounded'
  const handleClass = isAnalyzing ? '!bg-gray-400' : '!bg-blue-500'
  const metricBorderClass = isAnalyzing ? 'border-gray-300 dark:border-gray-600' : 'border-blue-200 dark:border-blue-800'
  const metricValueClass = isAnalyzing ? 'font-bold text-gray-500 dark:text-gray-400' : 'font-bold text-green-600 dark:text-green-400'

  return (
    <div className={containerClass}>
      <Handle type="target" position={Position.Top} className={handleClass} />

      <div className="space-y-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`${iconBgClass} p-1 rounded`}>
              {isAnalyzing ? (
                <Loader2 className={`${iconClass} animate-spin`} />
              ) : (
                <TrendingUp className={iconClass} />
              )}
            </div>
            <div className={titleClass}>
              {isAnalyzing ? 'Analyzing...' : 'Analytics'}
              {data.iterationNumber !== undefined && (
                <span className={`ml-1 ${subtitleClass}`}>
                  (Iter {data.iterationNumber as number})
                </span>
              )}
            </div>
          </div>
          <div className={badgeClass}>
            {isAnalyzing ? 'Pending' : `${data.winnerCount as number} Winners`}
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="flex gap-2 text-xs">
          <div className={`flex-1 bg-white dark:bg-gray-800 p-1.5 rounded border ${metricBorderClass} text-center`}>
            <div className={metricValueClass}>
              {isAnalyzing ? '--' : (data.improvements as AnalyticsNodeData['improvements']).clickRate}
            </div>
            <div className="text-muted-foreground text-xs">CTR</div>
          </div>
          <div className={`flex-1 bg-white dark:bg-gray-800 p-1.5 rounded border ${metricBorderClass} text-center`}>
            <div className={metricValueClass}>
              {isAnalyzing ? '--' : (data.improvements as AnalyticsNodeData['improvements']).conversionRate}
            </div>
            <div className="text-muted-foreground text-xs">CVR</div>
          </div>
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className={handleClass} />
    </div>
  )
})

AnalyticsNode.displayName = 'AnalyticsNode'
