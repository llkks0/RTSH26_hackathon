import {useMemo} from 'react'
import {useQuery} from '@tanstack/react-query'
import {CAMPAIGNS_QUERY_KEY} from './useCampaigns'
import {apiClient} from '../client'
import {transformCampaignFullToGraphData} from '@/lib/transformCampaignData'
import type {CampaignGraphData} from '@/lib/mockFlowData'
import type {CampaignFull, FlowStepState} from '../types'

const POLL_INTERVAL = 10000 // 10 seconds

/**
 * Determine if the campaign is still in progress (has non-completed steps)
 */
function isCampaignInProgress(campaign: CampaignFull): boolean {
    const nonCompletedStates: FlowStepState[] = ['generating', 'collecting', 'analyzing']

    for (const flow of campaign.campaign_flows) {
        for (const step of flow.steps) {
            if (nonCompletedStates.includes(step.state)) {
                return true
            }
        }
    }
    return false
}

/**
 * Get the current state of the campaign for display purposes
 */
function getCampaignState(campaign: CampaignFull): 'idle' | 'in_progress' | 'completed' {
    if (campaign.campaign_flows.length === 0) {
        return 'idle'
    }

    // Check all steps across all flows
    const allSteps = campaign.campaign_flows.flatMap(flow => flow.steps)
    if (allSteps.length === 0) {
        return 'idle'
    }

    const hasNonCompleted = allSteps.some(step => step.state !== 'completed')
    return hasNonCompleted ? 'in_progress' : 'completed'
}

/**
 * Hook to fetch the complete campaign graph data in a single API call.
 *
 * Uses the /campaigns/{id}/full endpoint which returns the campaign with
 * all flows, steps, and results nested in a single response.
 *
 * Automatically polls every 10 seconds while the campaign is in progress.
 */
export function useCampaignGraphData(campaignId: string) {
    const {data: campaignFull, isLoading, error, isFetching} = useQuery({
        queryKey: [CAMPAIGNS_QUERY_KEY, campaignId, 'full'],
        queryFn: () => apiClient.getCampaignFull(campaignId),
        enabled: !!campaignId,
        refetchInterval: (query) => {
            const data = query.state.data
            if (!data) return false
            // Poll while campaign is in progress
            return isCampaignInProgress(data) ? POLL_INTERVAL : false
        },
    })

    // Transform data when loaded - memoize to prevent unnecessary recalculations
    const graphData = useMemo<CampaignGraphData | null>(() => {
        if (!campaignFull) return null
        return transformCampaignFullToGraphData(campaignFull)
    }, [campaignFull])

    // Check if we have flows but no steps (empty campaign)
    const isEmpty = graphData && graphData.targetGroups.every(tg => tg.iterations.length === 0)

    // Determine campaign state
    const campaignState = campaignFull ? getCampaignState(campaignFull) : 'idle'
    const isInProgress = campaignState === 'in_progress'

    return {
        data: graphData,
        rawData: campaignFull,
        isLoading,
        isFetching,
        error,
        isEmpty: isEmpty || false,
        campaignState,
        isInProgress,
    }
}
