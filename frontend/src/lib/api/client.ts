import type {
    Asset,
    AssetCreate,
    AssetListParams,
    AssetUpdate,
    Campaign,
    CampaignCreate,
    CampaignFlow,
    CampaignFull,
    CampaignSpec,
    CampaignSpecCreate,
    CampaignSpecUpdate,
    FlowStep,
    GeneratedImage,
    PaginationParams,
    TargetGroup,
    TargetGroupCreate,
    TargetGroupUpdate,
} from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

class ApiClient {
    private baseUrl: string

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl
    }

    private async request<T>(
        endpoint: string,
        options?: RequestInit
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers,
            },
        })

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`)
        }

        if (response.status === 204) {
            return undefined as T
        }

        return response.json()
    }

    // ---------------------------------------------------------
    // Assets
    // ---------------------------------------------------------

    async getAssets(params?: AssetListParams): Promise<Asset[]> {
        const searchParams = new URLSearchParams()
        if (params?.skip !== undefined) searchParams.set('skip', String(params.skip))
        if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))
        if (params?.asset_type) searchParams.set('asset_type', params.asset_type)

        const query = searchParams.toString()
        return this.request<Asset[]>(`/assets/${query ? `?${query}` : ''}`)
    }

    async getAsset(assetId: string): Promise<Asset> {
        return this.request<Asset>(`/assets/${assetId}`)
    }

    async createAsset(data: AssetCreate): Promise<Asset> {
        return this.request<Asset>('/assets/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
    }

    async updateAsset(assetId: string, data: AssetUpdate): Promise<Asset> {
        return this.request<Asset>(`/assets/${assetId}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        })
    }

    async deleteAsset(assetId: string): Promise<void> {
        return this.request<void>(`/assets/${assetId}`, {
            method: 'DELETE',
        })
    }

    async uploadAsset(formData: FormData): Promise<Asset> {
        const url = `${this.baseUrl}/assets/upload`
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            // Don't set Content-Type header - browser will set it with boundary for multipart/form-data
        })

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`)
        }

        return response.json()
    }

    getAssetFileUrl(filename: string): string {
        return `${this.baseUrl}/assets/files/${filename}`
    }

    getGeneratedImageFileUrl(filename: string): string {
return `${this.baseUrl}/campaigns/${filename}`
    }

    // ---------------------------------------------------------
    // Target Groups
    // ---------------------------------------------------------

    async getTargetGroups(params?: PaginationParams): Promise<TargetGroup[]> {
        const searchParams = new URLSearchParams()
        if (params?.skip !== undefined) searchParams.set('skip', String(params.skip))
        if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))

        const query = searchParams.toString()
        return this.request<TargetGroup[]>(`/target-groups/${query ? `?${query}` : ''}`)
    }

    async getTargetGroup(targetGroupId: string): Promise<TargetGroup> {
        return this.request<TargetGroup>(`/target-groups/${targetGroupId}`)
    }

    async createTargetGroup(data: TargetGroupCreate): Promise<TargetGroup> {
        return this.request<TargetGroup>('/target-groups/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
    }

    async updateTargetGroup(targetGroupId: string, data: TargetGroupUpdate): Promise<TargetGroup> {
        return this.request<TargetGroup>(`/target-groups/${targetGroupId}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        })
    }

    async deleteTargetGroup(targetGroupId: string): Promise<void> {
        return this.request<void>(`/target-groups/${targetGroupId}`, {
            method: 'DELETE',
        })
    }

    // ---------------------------------------------------------
    // Campaign Specs
    // ---------------------------------------------------------

    async getCampaignSpecs(params?: PaginationParams): Promise<CampaignSpec[]> {
        const searchParams = new URLSearchParams()
        if (params?.skip !== undefined) searchParams.set('skip', String(params.skip))
        if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))

        const query = searchParams.toString()
        return this.request<CampaignSpec[]>(`/campaign-specs/${query ? `?${query}` : ''}`)
    }

    async getCampaignSpec(id: string): Promise<CampaignSpec> {
        return this.request<CampaignSpec>(`/campaign-specs/${id}`)
    }

    async createCampaignSpec(data: CampaignSpecCreate): Promise<CampaignSpec> {
        return this.request<CampaignSpec>('/campaign-specs/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
    }

    async updateCampaignSpec(id: string, data: CampaignSpecUpdate): Promise<CampaignSpec> {
        return this.request<CampaignSpec>(`/campaign-specs/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        })
    }

    async deleteCampaignSpec(id: string): Promise<void> {
        return this.request<void>(`/campaign-specs/${id}`, {
            method: 'DELETE',
        })
    }

    async getCampaignSpecAssets(id: string): Promise<Asset[]> {
        return this.request<Asset[]>(`/campaign-specs/${id}/assets`)
    }

    async addCampaignSpecAsset(id: string, assetId: string): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/campaign-specs/${id}/assets/${assetId}`, {
            method: 'POST',
        })
    }

    async removeCampaignSpecAsset(id: string, assetId: string): Promise<void> {
        return this.request<void>(`/campaign-specs/${id}/assets/${assetId}`, {
            method: 'DELETE',
        })
    }

    async getCampaignSpecTargetGroups(id: string): Promise<TargetGroup[]> {
        return this.request<TargetGroup[]>(`/campaign-specs/${id}/target-groups`)
    }

    async addCampaignSpecTargetGroup(id: string, targetGroupId: string): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/campaign-specs/${id}/target-groups/${targetGroupId}`, {
            method: 'POST',
        })
    }

    async removeCampaignSpecTargetGroup(id: string, targetGroupId: string): Promise<void> {
        return this.request<void>(`/campaign-specs/${id}/target-groups/${targetGroupId}`, {
            method: 'DELETE',
        })
    }

    // ---------------------------------------------------------
    // Campaigns
    // ---------------------------------------------------------

    async getCampaigns(params?: PaginationParams): Promise<Campaign[]> {
        const searchParams = new URLSearchParams()
        if (params?.skip !== undefined) searchParams.set('skip', String(params.skip))
        if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))

        const query = searchParams.toString()
        return this.request<Campaign[]>(`/campaigns/${query ? `?${query}` : ''}`)
    }

    async getCampaign(id: string): Promise<Campaign> {
        return this.request<Campaign>(`/campaigns/${id}`)
    }

    async getCampaignFull(id: string): Promise<CampaignFull> {
        return this.request<CampaignFull>(`/campaigns/${id}/full`)
    }

    async createCampaign(data: CampaignCreate): Promise<Campaign> {
        return this.request<Campaign>('/campaigns/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
    }

    async getCampaignFlows(campaignId: string): Promise<CampaignFlow[]> {
        return this.request<CampaignFlow[]>(`/campaigns/${campaignId}/flows`)
    }

    async getCampaignFlow(campaignId: string, flowId: string): Promise<CampaignFlow> {
        return this.request<CampaignFlow>(`/campaigns/${campaignId}/flows/${flowId}`)
    }

    async getFlowSteps(campaignId: string, flowId: string): Promise<FlowStep[]> {
        return this.request<FlowStep[]>(`/campaigns/${campaignId}/flows/${flowId}/steps`)
    }

    async getFlowStep(campaignId: string, flowId: string, stepId: string): Promise<FlowStep> {
        return this.request<FlowStep>(`/campaigns/${campaignId}/flows/${flowId}/steps/${stepId}`)
    }

    async getStepImages(campaignId: string, flowId: string, stepId: string): Promise<GeneratedImage[]> {
        return this.request<GeneratedImage[]>(`/campaigns/${campaignId}/flows/${flowId}/steps/${stepId}/images`)
    }

    async getCampaignBySpecId(campaignSpecId: string): Promise<Campaign | null> {
        const campaigns = await this.getCampaigns()
        return campaigns.find(c => c.campaign_spec_id === campaignSpecId) || null
    }

    async getOrCreateCampaignFromSpec(campaignSpecId: string): Promise<Campaign> {
        // Try to find existing campaign
        const existing = await this.getCampaignBySpecId(campaignSpecId)
        if (existing) {
            return existing
        }

        // Create new campaign
        return this.createCampaign({campaign_spec_id: campaignSpecId})
    }
}

export const apiClient = new ApiClient(API_BASE_URL)
