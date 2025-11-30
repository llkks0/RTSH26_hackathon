import {X} from 'lucide-react'
import {Button} from '@/components/ui/button'
import type {Node} from '@xyflow/react'
import type {ImageNodeData} from './nodes/ImageNode'
import type {AnalyticsNodeData} from './nodes/AnalyticsNode'
import type {EnhancementNodeData} from './nodes/EnhancementNode'

interface GraphSidebarProps {
    selectedNode: Node | null
    onClose: () => void
}

export function GraphSidebar({selectedNode, onClose}: GraphSidebarProps) {
    if (!selectedNode) return null

    const renderNodeDetails = () => {
        switch (selectedNode.type) {
            case 'prompt':
                return (
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-medium text-muted-foreground mb-2">
                                Base Prompt
                            </h3>
                            <p className="text-sm">{selectedNode.data.prompt as string}</p>
                        </div>
                    </div>
                )

            case 'enhancement': {
                const enhancementData = selectedNode.data as EnhancementNodeData
                return (
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-medium text-muted-foreground mb-2">
                                {(enhancementData.title as string) || 'Enhanced Prompt'}
                            </h3>
                            <p className="text-sm">{enhancementData.prompt as string}</p>
                        </div>

                        {enhancementData.notes && (
                            <div className="p-3 bg-primary/5 rounded-lg">
                                <p className="text-xs font-medium mb-1">Notes:</p>
                                <p className="text-xs text-muted-foreground">{enhancementData.notes as string}</p>
                            </div>
                        )}

                        {enhancementData.usedAssets && (enhancementData.usedAssets as string[]).length > 0 && (
                            <div>
                                <h4 className="text-sm font-medium mb-2">Used Assets</h4>
                                <div className="space-y-1">
                                    {(enhancementData.usedAssets as string[]).map((asset, idx) => (
                                        <div key={idx} className="text-xs p-2 bg-muted rounded">
                                            {asset}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {!enhancementData.notes && !enhancementData.usedAssets && (
                            <div className="p-3 bg-primary/5 rounded-lg">
                                <p className="text-xs text-muted-foreground">
                                    This prompt has been enhanced using AI to improve engagement and clarity.
                                </p>
                            </div>
                        )}
                    </div>
                )
            }

            case 'targetGroup':
                return (
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-medium text-muted-foreground mb-2">
                                Target Group
                            </h3>
                            <p className="text-sm font-medium">{selectedNode.data.name as string}</p>
                        </div>
                    </div>
                )

            case 'image':
                return (
                    <div className="space-y-4">
                        <div className="aspect-square rounded-lg overflow-hidden bg-muted">
                            <img
                                src={selectedNode.data.imageUrl as string}
                                alt="Generated"
                                className="w-full h-full object-cover"
                            />
                        </div>

                        <div>
                            <h3 className="text-sm font-medium mb-2">
                                {(selectedNode.data.isWinner as boolean) ? '🏆 Winner Image' : 'Test Variant'}
                            </h3>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Click Rate</span>
                                    <span
                                        className="font-medium">{(selectedNode.data.analytics as ImageNodeData['analytics']).clickRate.toFixed(2)}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Conversion Rate</span>
                                    <span
                                        className="font-medium">{(selectedNode.data.analytics as ImageNodeData['analytics']).conversionRate.toFixed(2)}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Engagement</span>
                                    <span
                                        className="font-medium">{(selectedNode.data.analytics as ImageNodeData['analytics']).engagement.toFixed(2)}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Impressions</span>
                                    <span
                                        className="font-medium">{(selectedNode.data.analytics as ImageNodeData['analytics']).impressions.toLocaleString()}</span>
                                </div>
                            </div>
                        </div>

                        {(selectedNode.data.isWinner as boolean) && (
                            <div className="p-3 bg-green-50 dark:bg-green-950/30 border border-green-500/50 rounded-lg">
                                <p className="text-xs text-green-700 dark:text-green-300">
                                    This image outperformed other variants and was selected as a winner.
                                </p>
                            </div>
                        )}
                    </div>
                )

            case 'analytics': {
                const analyticsData = selectedNode.data as AnalyticsNodeData
                return (
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-medium text-muted-foreground mb-2">
                                {analyticsData.iterationNumber !== undefined
                                    ? `Iteration ${analyticsData.iterationNumber as number} Performance`
                                    : 'Campaign Performance'}
                            </h3>
                            <p className="text-sm">
                                Winner images have been identified based on performance metrics.
                            </p>
                        </div>

                        {analyticsData.differentiationText && (
                            <div>
                                <h4 className="text-sm font-medium mb-2">Insights</h4>
                                <p className="text-xs text-muted-foreground p-2 bg-muted rounded">
                                    {analyticsData.differentiationText as string}
                                </p>
                            </div>
                        )}

                        {analyticsData.differentiationTags && (analyticsData.differentiationTags as string[]).length > 0 && (
                            <div>
                                <h4 className="text-sm font-medium mb-2">Key Factors</h4>
                                <div className="flex flex-wrap gap-1">
                                    {(analyticsData.differentiationTags as string[]).map((tag, idx) => (
                                        <span key={idx}
                                              className="text-xs px-2 py-1 bg-primary/10 text-primary rounded">
                      {tag}
                    </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div>
                            <h4 className="text-sm font-medium mb-2">Performance Improvements</h4>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm p-2 bg-muted rounded">
                                    <span className="text-muted-foreground">Click Rate</span>
                                    <span className="font-medium text-green-600 dark:text-green-400">
                    {(analyticsData.improvements as AnalyticsNodeData['improvements']).clickRate}
                  </span>
                                </div>
                                <div className="flex justify-between text-sm p-2 bg-muted rounded">
                                    <span className="text-muted-foreground">Conversion Rate</span>
                                    <span className="font-medium text-green-600 dark:text-green-400">
                    {(analyticsData.improvements as AnalyticsNodeData['improvements']).conversionRate}
                  </span>
                                </div>
                                <div className="flex justify-between text-sm p-2 bg-muted rounded">
                                    <span className="text-muted-foreground">Engagement</span>
                                    <span className="font-medium text-green-600 dark:text-green-400">
                    {(analyticsData.improvements as AnalyticsNodeData['improvements']).engagement}
                  </span>
                                </div>
                            </div>
                        </div>
                    </div>
                )
            }

            default:
                return <p className="text-sm text-muted-foreground">No details available</p>
        }
    }

    return (
        <div className="absolute right-0 top-0 h-full w-96 bg-card border-l border-border shadow-xl z-10">
            <div className="flex items-center justify-between p-4 border-b border-border">
                <h2 className="text-lg font-semibold">Node Details</h2>
                <Button variant="ghost" size="icon" onClick={onClose}>
                    <X className="h-4 w-4"/>
                </Button>
            </div>

            <div className="p-4 overflow-y-auto h-[calc(100%-64px)]">
                {renderNodeDetails()}
            </div>
        </div>
    )
}
