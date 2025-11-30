import type {
  CampaignFull,
  CampaignFlowFull,
  FlowStepFull,
  GeneratedImageFull,
  ImageMetrics,
} from './api/types'
import type {
  CampaignGraphData,
  TargetGroupBranch,
  Iteration,
  GeneratedImage as GraphGeneratedImage,
} from './mockFlowData'
import { apiClient } from './api/client'

/**
 * Transform the full campaign response from the backend into CampaignGraphData format.
 * This is the new transform function that works with the /campaigns/{id}/full endpoint.
 */
export function transformCampaignFullToGraphData(campaign: CampaignFull): CampaignGraphData {
  const campaignSpec = campaign.campaign_spec

  return {
    campaignId: campaign.id,
    campaignName: campaignSpec?.name || 'Unnamed Campaign',
    basePrompt: campaignSpec?.base_prompt || '',
    enhancedPrompt: campaignSpec?.base_prompt || '', // TODO: get actual enhanced prompt from first step
    targetGroups: campaign.campaign_flows.map(flow => transformFlowToBranch(flow)),
  }
}

function transformFlowToBranch(flow: CampaignFlowFull): TargetGroupBranch {
  return {
    id: flow.id,
    name: flow.target_group?.name || 'Unknown Target Group',
    iterations: flow.steps
      .sort((a, b) => a.iteration - b.iteration)
      .map(step => transformStepToIteration(step)),
  }
}

function transformStepToIteration(step: FlowStepFull): Iteration {
  const generationResult = step.generation_result
  const analysisResult = step.analysis_result
  const generatedImages = generationResult?.generated_images || []

  return {
    iterationNumber: step.iteration,
    promptGen: {
      prompt: generationResult?.prompt || '',
      usedAssets: generationResult?.selected_assets?.map(asset => asset.name) || [],
      notes: generationResult?.prompt_notes || undefined,
    },
    imageGen: {
      generatedImages: generatedImages.map(img =>
        transformImageToGraphImage(img, analysisResult?.winner_image_ids || [])
      ),
    },
    analytics: {
      winnerImages: analysisResult?.winner_image_ids || [],
      differentiationText: analysisResult?.qualitative_diff || '',
      differentiationTags: analysisResult?.diff_tags || [],
      improvements: calculateImprovements(generatedImages, analysisResult?.winner_image_ids || []),
    },
  }
}

function transformImageToGraphImage(
  image: GeneratedImageFull,
  winnerIds: string[]
): GraphGeneratedImage {
  const metrics = image.metrics

  return {
    id: image.id,
    imageUrl: apiClient.getAssetFileUrl(image.file_name),
    isWinner: winnerIds.includes(image.id),
    analytics: {
      clickRate: metrics?.ctr ? metrics.ctr * 100 : 0,
      conversionRate: metrics?.conversion_rate ? metrics.conversion_rate * 100 : 0,
      engagement: calculateEngagement(metrics),
      impressions: metrics?.impressions || 0,
    },
  }
}

function calculateEngagement(metrics: ImageMetrics | null | undefined): number {
  if (!metrics) return 0
  // Simple engagement calculation: (clicks + conversions) / impressions * 100
  if (metrics.impressions === 0) return 0
  return ((metrics.clicks + metrics.conversions) / metrics.impressions) * 100
}

function calculateImprovements(
  images: GeneratedImageFull[],
  winnerIds: string[]
): { clickRate: string; conversionRate: string; engagement: string } {
  const winners = images.filter(img => winnerIds.includes(img.id))

  if (winners.length === 0) {
    return {
      clickRate: '0%',
      conversionRate: '0%',
      engagement: '0%',
    }
  }

  // Calculate average metrics for winners
  const avgCtr = winners.reduce((sum, img) => sum + (img.metrics?.ctr || 0), 0) / winners.length
  const avgConversionRate =
    winners.reduce((sum, img) => sum + (img.metrics?.conversion_rate || 0), 0) / winners.length
  const avgEngagement =
    winners.reduce((sum, img) => sum + calculateEngagement(img.metrics), 0) / winners.length

  return {
    clickRate: `${(avgCtr * 100).toFixed(2)}%`,
    conversionRate: `${(avgConversionRate * 100).toFixed(2)}%`,
    engagement: `${avgEngagement.toFixed(0)}%`,
  }
}
