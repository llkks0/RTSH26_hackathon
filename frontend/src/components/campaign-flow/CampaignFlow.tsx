import { useState, useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Node,
  Edge,
  NodeTypes,
  OnNodesChange,
  OnEdgesChange,
  applyNodeChanges,
  applyEdgeChanges,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Button } from '@/components/ui/button'
import { Settings } from 'lucide-react'
import { getMockFlowData } from '@/lib/mockFlowData'
import { PromptNode } from './nodes/PromptNode'
import { EnhancementNode } from './nodes/EnhancementNode'
import { TargetGroupNode } from './nodes/TargetGroupNode'
import { ImageNode } from './nodes/ImageNode'
import { AnalyticsNode } from './nodes/AnalyticsNode'
import { FlowSidebar } from './FlowSidebar'
import { generateFlowLayout } from './utils/generateFlowLayout'

interface CampaignFlowProps {
  campaignId: string
}

const nodeTypes: NodeTypes = {
  prompt: PromptNode,
  enhancement: EnhancementNode,
  targetGroup: TargetGroupNode,
  image: ImageNode,
  analytics: AnalyticsNode,
}

export function CampaignFlow({ campaignId }: CampaignFlowProps) {
  const flowData = getMockFlowData(campaignId)
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => generateFlowLayout(flowData),
    [flowData]
  )

  const [nodes, setNodes] = useState<Node[]>(initialNodes)
  const [edges, setEdges] = useState<Edge[]>(initialEdges)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

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

  return (
    <div className="relative w-full h-screen">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 h-16 bg-background/95 backdrop-blur border-b border-border z-10 flex items-center justify-between px-6">
        <div>
          <h1 className="text-xl font-bold">{flowData.campaignName}</h1>
          <p className="text-sm text-muted-foreground">Campaign Flow Visualization</p>
        </div>
        <Button variant="outline" size="icon">
          <Settings className="h-4 w-4" />
        </Button>
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
          defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
        >
          <Background />
        </ReactFlow>
      </div>

      {/* Sidebar */}
      <FlowSidebar
        selectedNode={selectedNode}
        onClose={() => setSelectedNode(null)}
      />
    </div>
  )
}
