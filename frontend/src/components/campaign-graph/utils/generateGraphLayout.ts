import { Node, Edge } from '@xyflow/react'
import type { CampaignGraphData } from '@/lib/mockFlowData'

const HORIZONTAL_SPACING = 450
const VERTICAL_SPACING = 200
const IMAGE_HORIZONTAL_SPACING = 220
const ITERATION_VERTICAL_SPACING = 250

// Node widths for centering
const NODE_WIDTHS = {
  prompt: 320,
  enhancement: 320,
  targetGroup: 280,
  image: 200,
  analytics: 280,
}

/**
 * Generate the React Flow layout from CampaignGraphData.
 * Creates nodes and edges for the complete campaign graph visualization.
 */
export function generateGraphLayout(graphData: CampaignGraphData): {
  nodes: Node[]
  edges: Edge[]
} {
  const nodes: Node[] = []
  const edges: Edge[] = []

  // Calculate center position for initial nodes
  const centerX = 400

  // 1. Base Prompt Node
  nodes.push({
    id: 'prompt',
    type: 'prompt',
    position: { x: centerX - NODE_WIDTHS.prompt / 2, y: 0 },
    data: { prompt: graphData.basePrompt },
  })

  // 2. Enhanced Prompt Node
  nodes.push({
    id: 'enhancement',
    type: 'enhancement',
    position: { x: centerX - NODE_WIDTHS.enhancement / 2, y: VERTICAL_SPACING },
    data: { prompt: graphData.enhancedPrompt },
  })

  edges.push({
    id: 'e-prompt-enhancement',
    source: 'prompt',
    target: 'enhancement',
    animated: true,
  })

  // 3. Target Group branches with iterations
  // Each targetGroup represents a CampaignFlow from the backend (one branch per target group)
  const numTargetGroups = graphData.targetGroups.length
  const targetGroupStartY = VERTICAL_SPACING * 2

  graphData.targetGroups.forEach((targetGroup, tgIndex) => {
    // Calculate x position to spread target groups horizontally
    const tgX = centerX + (tgIndex - (numTargetGroups - 1) / 2) * (HORIZONTAL_SPACING * 5)

    // Target Group Node
    const tgNodeId = `tg-${targetGroup.id}`
    nodes.push({
      id: tgNodeId,
      type: 'targetGroup',
      position: { x: tgX - NODE_WIDTHS.targetGroup / 2, y: targetGroupStartY },
      data: { name: targetGroup.name },
    })

    edges.push({
      id: `e-enhancement-${tgNodeId}`,
      source: 'enhancement',
      target: tgNodeId,
      animated: true,
    })

    let previousNodeId = tgNodeId
    let currentY = targetGroupStartY + VERTICAL_SPACING

    // Process each iteration
    targetGroup.iterations.forEach((iteration) => {
      const iterPrefix = `${targetGroup.id}-iter${iteration.iterationNumber}`

      // PromptGen Node
      const promptGenId = `promptgen-${iterPrefix}`
      nodes.push({
        id: promptGenId,
        type: 'enhancement',
        position: { x: tgX - NODE_WIDTHS.enhancement / 2, y: currentY },
        data: {
          prompt: iteration.promptGen.prompt,
          title: `Iteration ${iteration.iterationNumber} - PromptGen`,
          notes: iteration.promptGen.notes,
          usedAssets: iteration.promptGen.usedAssets,
        },
      })

      edges.push({
        id: `e-${previousNodeId}-${promptGenId}`,
        source: previousNodeId,
        target: promptGenId,
        animated: true,
      })

      currentY += VERTICAL_SPACING

      // Image Nodes - middle image centered at tgX, others evenly spaced
      const imageNodeIds: string[] = []
      const numImages = iteration.imageGen.generatedImages.length
      const middleIndex = Math.floor(numImages / 2)
      const imagesY = currentY

      iteration.imageGen.generatedImages.forEach((image, imgIndex) => {
        const imageNodeId = `image-${image.id}`
        imageNodeIds.push(imageNodeId)
        // Position relative to middle image: middle is centered at tgX, others offset by spacing
        const imageX = tgX + (imgIndex - middleIndex) * IMAGE_HORIZONTAL_SPACING - NODE_WIDTHS.image / 2

        nodes.push({
          id: imageNodeId,
          type: 'image',
          position: { x: imageX, y: imagesY },
          data: image,
        })

        edges.push({
          id: `e-${promptGenId}-${imageNodeId}`,
          source: promptGenId,
          target: imageNodeId,
          animated: true,
        })
      })

      // Account for image node height (~220px) + spacing
      currentY += 220 + VERTICAL_SPACING

      // Analytics Node
      const analyticsId = `analytics-${iterPrefix}`
      nodes.push({
        id: analyticsId,
        type: 'analytics',
        position: { x: tgX - NODE_WIDTHS.analytics / 2, y: currentY },
        data: {
          winnerCount: iteration.analytics.winnerImages.length,
          improvements: iteration.analytics.improvements,
          differentiationText: iteration.analytics.differentiationText,
          differentiationTags: iteration.analytics.differentiationTags,
          iterationNumber: iteration.iterationNumber,
        },
      })

      // Connect all images to analytics
      imageNodeIds.forEach((imageId) => {
        edges.push({
          id: `e-${imageId}-${analyticsId}`,
          source: imageId,
          target: analyticsId,
          animated: true,
        })
      })

      // Set up for next iteration
      previousNodeId = analyticsId
      currentY += ITERATION_VERTICAL_SPACING
    })
  })

  return { nodes, edges }
}
