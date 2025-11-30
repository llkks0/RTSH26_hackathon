import {useCallback, useEffect, useMemo, useState} from 'react'
import {
    applyEdgeChanges,
    applyNodeChanges,
    Background,
    Edge,
    Node,
    NodeTypes,
    OnEdgesChange,
    OnNodesChange,
    ReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {Button} from '@/components/ui/button'
import {FileText} from 'lucide-react'
import {useCampaignGraphData} from '@/lib/api/hooks/useCampaignGraphData'
import {PromptNode} from './nodes/PromptNode'
import {EnhancementNode} from './nodes/EnhancementNode'
import {TargetGroupNode} from './nodes/TargetGroupNode'
import {ImageNode} from './nodes/ImageNode'
import {AnalyticsNode} from './nodes/AnalyticsNode'
import {GraphSidebar} from './GraphSidebar'
import {CampaignSpecDialog} from './CampaignSpecDialog'
import {generateGraphLayout} from './utils/generateGraphLayout'

interface CampaignGraphProps {
    campaignId: string
}

const nodeTypes: NodeTypes = {
    prompt: PromptNode,
    enhancement: EnhancementNode,
    targetGroup: TargetGroupNode,
    image: ImageNode,
    analytics: AnalyticsNode,
}

/**
 * CampaignGraph - Visualizes the complete campaign with all target group flows.
 *
 * This component renders the full campaign graph showing:
 * - The base prompt and enhanced prompt at the top
 * - Target group branches (each representing a CampaignFlow from the backend)
 * - Iterations within each target group flow
 * - Generated images and analytics for each iteration
 */
export function CampaignGraph({campaignId}: CampaignGraphProps) {
    const {data: graphData, rawData, isLoading, error, isEmpty, isInProgress} = useCampaignGraphData(campaignId)

    const {nodes: initialNodes, edges: initialEdges} = useMemo(
        () => graphData ? generateGraphLayout(graphData) : {nodes: [], edges: []},
        [graphData]
    )

    const [nodes, setNodes] = useState<Node[]>(initialNodes)
    const [edges, setEdges] = useState<Edge[]>(initialEdges)
    const [selectedNode, setSelectedNode] = useState<Node | null>(null)
    const [specDialogOpen, setSpecDialogOpen] = useState(false)

    // Sync state when graph data loads/changes
    // Only update if we have actual content to prevent resetting during refetches
    useEffect(() => {
        if (initialNodes.length > 0) {
            setNodes(initialNodes)
        }
        if (initialEdges.length > 0) {
            setEdges(initialEdges)
        }
    }, [initialNodes, initialEdges])

    const onNodesChange: OnNodesChange = useCallback(
        (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
        []
    )

    const onEdgesChange: OnEdgesChange = useCallback(
        (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
        []
    )

    const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
        setSelectedNode(node)
    }, [])

    const onPaneClick = useCallback(() => {
        setSelectedNode(null)
    }, [])

    if (error) {
        return (
            <div className="relative w-full h-screen flex items-center justify-center">
                <div className="text-center">
                    <h2 className="text-2xl font-bold mb-2">Error loading campaign</h2>
                    <p className="text-muted-foreground">
                        {error.message}
                    </p>
                </div>
            </div>
        )
    }

    if (isLoading || !graphData) {
        return (
            <div className="relative w-full h-screen flex items-center justify-center">
                <div className="text-center">
                    <h2 className="text-2xl font-bold mb-2">Loading campaign graph...</h2>
                    <p className="text-muted-foreground">Please wait while we fetch the data</p>
                </div>
            </div>
        )
    }

    if (isEmpty) {
        return (
            <div className="relative w-full h-screen">
                <div
                    className="absolute top-0 left-0 right-0 h-16 bg-background/95 backdrop-blur border-b border-border z-10 flex items-center justify-between px-6">
                    <div>
                        <h1 className="text-xl font-bold">{graphData.campaignName}</h1>
                        <p className="text-sm text-muted-foreground">Campaign Graph</p>
                    </div>
                </div>
                <div className="flex items-center justify-center h-full pt-16">
                    <div className="text-center">
                        <h2 className="text-2xl font-bold mb-2">Campaign Not Started</h2>
                        <p className="text-muted-foreground mb-4">
                            This campaign has been created but hasn't started generating content yet.
                        </p>
                        <p className="text-sm text-muted-foreground">
                            Use the campaign generation endpoints to start creating iterations.
                        </p>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="relative w-full h-screen">
            {/* Header */}
            <div
                className="absolute top-0 left-0 right-0 h-16 bg-background/95 backdrop-blur border-b border-border z-10 flex items-center justify-between px-6">
                <div>
                    <h1 className="text-xl font-bold">{graphData.campaignName}</h1>
                    <p className="text-sm text-muted-foreground">Campaign Graph</p>
                </div>
                <div className="flex items-center gap-3">

                    <Button variant="outline" onClick={() => setSpecDialogOpen(true)}>
                        <FileText className="h-4 w-4 mr-2"/>
                        View Spec
                    </Button>

                    {isInProgress && (
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary">
                            <span className="text-sm font-medium">In Progress</span>
                            <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75">
                </span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary">
                </span>
                        </span>
                        </div>
                    )}
                </div>
            </div>

            {/* React Flow Canvas */}
            <div className="w-full h-full pt-16">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onNodeClick={onNodeClick}
                    onPaneClick={onPaneClick}
                    nodeTypes={nodeTypes}
                    nodesDraggable={false}
                    nodesConnectable={false}
                    elementsSelectable={true}
                    fitView
                    minZoom={0.5}
                    maxZoom={1.5}
                    defaultViewport={{x: 0, y: 0, zoom: 0.8}}
                >
                    <Background/>
                </ReactFlow>
            </div>

            {/* Sidebar */}
            <GraphSidebar
                selectedNode={selectedNode}
                onClose={() => setSelectedNode(null)}
            />

            {/* Campaign Spec Dialog */}
            <CampaignSpecDialog
                open={specDialogOpen}
                onOpenChange={setSpecDialogOpen}
                campaign={rawData ?? null}
            />
        </div>
    )
}
