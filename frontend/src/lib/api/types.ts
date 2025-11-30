// ---------------------------------------------------------
// Enums
// ---------------------------------------------------------

export type AssetType =
  | 'background'
  | 'product'
  | 'model'
  | 'logo'
  | 'slogan'
  | 'tagline'
  | 'headline'
  | 'description'
  | 'cta'

// ---------------------------------------------------------
// Asset DTOs
// ---------------------------------------------------------

export interface Asset {
  id: string
  created_at: string
  name: string
  file_name: string
  asset_type: AssetType
  caption: string
  tags: string[]
  embedding: number[] | null
}

export interface AssetCreate {
  name: string
  file_name: string
  asset_type: AssetType
  caption: string
  tags?: string[]
  embedding?: number[] | null
}

export interface AssetUpdate {
  name?: string
  file_name?: string
  asset_type?: AssetType
  caption?: string
  tags?: string[]
  embedding?: number[] | null
}

// ---------------------------------------------------------
// Target Group DTOs
// ---------------------------------------------------------

export interface TargetGroup {
  id: string
  created_at: string
  name: string
  city: string | null
  age_group: string | null
  economic_status: string | null
  description: string | null
}

export interface TargetGroupCreate {
  name: string
  city?: string | null
  age_group?: string | null
  economic_status?: string | null
  description?: string | null
}

export interface TargetGroupUpdate {
  name?: string
  city?: string | null
  age_group?: string | null
  economic_status?: string | null
  description?: string | null
}

// ---------------------------------------------------------
// Campaign Spec DTOs
// ---------------------------------------------------------

export interface CampaignSpec {
  id: string
  created_at: string
  name: string
  base_prompt: string
  max_iterations: number
  target_group_ids: string[]
}

export interface CampaignSpecCreate {
  name: string
  base_prompt: string
  max_iterations?: number // defaults to 2
  target_group_ids?: string[]
}

export interface CampaignSpecUpdate {
  name?: string
  base_prompt?: string
  max_iterations?: number
  target_group_ids?: string[]
}

// ---------------------------------------------------------
// Campaign DTOs
// ---------------------------------------------------------

export type FlowStepState = 'generating' | 'collecting' | 'analyzing' | 'completed'

export interface Campaign {
  id: string
  created_at: string
  campaign_spec_id: string
  campaign_spec?: CampaignSpec
  campaign_flows?: CampaignFlow[]
}

export interface CampaignFlow {
  id: string
  created_at: string
  campaign_id: string
  target_group_id: string
  target_group?: TargetGroup
  steps?: FlowStep[]
}

export interface FlowStep {
  id: string
  created_at: string
  flow_id: string
  iteration: number
  state: FlowStepState
  input_embedding: number[] | null
  input_insights: string | null
  generation_result?: GenerationResult
  analysis_result?: AnalysisResult
}

export interface GenerationResult {
  id: string
  created_at: string
  step_id: string
  prompt: string
  prompt_notes: string | null
  selected_assets?: Asset[]
  generated_images?: GeneratedImage[]
}

export interface GeneratedImage {
  id: string
  created_at: string
  generation_result_id: string
  file_name: string
  metadata_tags: string[] | null
  model_version: string | null
  source_assets?: Asset[]
  metrics?: ImageMetrics
}

export interface ImageMetrics {
  id: string
  created_at: string
  image_id: string
  impressions: number
  clicks: number
  conversions: number
  cost: number
  ctr: number
  conversion_rate: number
  cpc: number
  cpa: number
}

export interface AnalysisResult {
  id: string
  created_at: string
  step_id: string
  winner_image_ids: string[]
  output_embedding: number[]
  qualitative_diff: string
  diff_tags: string[]
}

export interface CampaignCreate {
  campaign_spec_id: string
}

// ---------------------------------------------------------
// Full Campaign Response (nested)
// ---------------------------------------------------------

/**
 * Full campaign response with all nested data.
 * This is returned by GET /campaigns/{id}/full and includes
 * all flows, steps, generation results, and analysis results.
 */
export interface CampaignFull {
  id: string
  created_at: string
  campaign_spec_id: string
  campaign_spec: CampaignSpec | null
  campaign_flows: CampaignFlowFull[]
}

export interface CampaignFlowFull {
  id: string
  created_at: string
  campaign_id: string
  target_group_id: string
  target_group: TargetGroup | null
  steps: FlowStepFull[]
}

export interface FlowStepFull {
  id: string
  created_at: string
  flow_id: string
  iteration: number
  state: FlowStepState
  input_insights: string | null
  generation_result: GenerationResultFull | null
  analysis_result: AnalysisResultFull | null
}

export interface GenerationResultFull {
  id: string
  created_at: string
  step_id: string
  prompt: string
  prompt_notes: string | null
  selected_assets: Asset[]
  generated_images: GeneratedImageFull[]
}

export interface GeneratedImageFull {
  id: string
  created_at: string
  generation_result_id: string
  file_name: string
  metadata_tags: string[] | null
  model_version: string | null
  source_assets: Asset[]
  metrics: ImageMetrics | null
}

export interface AnalysisResultFull {
  id: string
  created_at: string
  step_id: string
  winner_image_ids: string[]
  qualitative_diff: string
  diff_tags: string[]
}

// ---------------------------------------------------------
// Query Parameters
// ---------------------------------------------------------

export interface PaginationParams {
  skip?: number // default: 0, min: 0
  limit?: number // default: 100, min: 1, max: 1000
}

export interface AssetListParams extends PaginationParams {
  asset_type?: AssetType
}
