import {useQuery} from '@tanstack/react-query'
import {CAMPAIGNS_QUERY_KEY} from './useCampaigns'
import {apiClient} from '../client'
import {transformCampaignFullToGraphData} from '@/lib/transformCampaignData'
import type {CampaignGraphData} from '@/lib/mockFlowData'

/**
 * Hook to fetch the complete campaign graph data in a single API call.
 *
 * Uses the /campaigns/{id}/full endpoint which returns the campaign with
 * all flows, steps, and results nested in a single response.
 */
export function useCampaignGraphData(campaignId: string) {
    const {data: campaignFull, isLoading, error} = useQuery({
        queryKey: [CAMPAIGNS_QUERY_KEY, campaignId, 'full'],
        queryFn: () => apiClient.getCampaignFull(campaignId),
        enabled: !!campaignId,
    })

    // Transform data when loaded
    const graphData: CampaignGraphData | null = campaignFull
        ? transformCampaignFullToGraphData(campaignFull)
        : null

    // Check if we have flows but no steps (empty campaign)
    const isEmpty = graphData && graphData.targetGroups.every(tg => tg.iterations.length === 0)

    return {
        data: graphData,
        isLoading,
        error,
        isEmpty: isEmpty || false,
    }
}
