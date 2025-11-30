import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { CampaignCreate, PaginationParams } from '../types'

export const CAMPAIGNS_QUERY_KEY = 'campaigns'

export function useCampaigns(params?: PaginationParams) {
  return useQuery({
    queryKey: [CAMPAIGNS_QUERY_KEY, params],
    queryFn: () => apiClient.getCampaigns(params),
  })
}

export function useCampaign(id: string) {
  return useQuery({
    queryKey: [CAMPAIGNS_QUERY_KEY, id],
    queryFn: () => apiClient.getCampaign(id),
    enabled: !!id,
  })
}

export function useCreateCampaign() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CampaignCreate) => apiClient.createCampaign(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGNS_QUERY_KEY] })
    },
  })
}

export function useCampaignFlows(campaignId: string) {
  return useQuery({
    queryKey: [CAMPAIGNS_QUERY_KEY, campaignId, 'flows'],
    queryFn: () => apiClient.getCampaignFlows(campaignId),
    enabled: !!campaignId,
  })
}

export function useCampaignFlow(campaignId: string, flowId: string) {
  return useQuery({
    queryKey: [CAMPAIGNS_QUERY_KEY, campaignId, 'flows', flowId],
    queryFn: () => apiClient.getCampaignFlow(campaignId, flowId),
    enabled: !!campaignId && !!flowId,
  })
}

export function useFlowSteps(campaignId: string, flowId: string) {
  return useQuery({
    queryKey: [CAMPAIGNS_QUERY_KEY, campaignId, 'flows', flowId, 'steps'],
    queryFn: () => apiClient.getFlowSteps(campaignId, flowId),
    enabled: !!campaignId && !!flowId,
  })
}

export function useFlowStep(campaignId: string, flowId: string, stepId: string) {
  return useQuery({
    queryKey: [CAMPAIGNS_QUERY_KEY, campaignId, 'flows', flowId, 'steps', stepId],
    queryFn: () => apiClient.getFlowStep(campaignId, flowId, stepId),
    enabled: !!campaignId && !!flowId && !!stepId,
  })
}

export function useStepImages(campaignId: string, flowId: string, stepId: string) {
  return useQuery({
    queryKey: [CAMPAIGNS_QUERY_KEY, campaignId, 'flows', flowId, 'steps', stepId, 'images'],
    queryFn: () => apiClient.getStepImages(campaignId, flowId, stepId),
    enabled: !!campaignId && !!flowId && !!stepId,
  })
}

export function useCampaignBySpecId(campaignSpecId: string) {
  return useQuery({
    queryKey: [CAMPAIGNS_QUERY_KEY, 'by-spec', campaignSpecId],
    queryFn: () => apiClient.getCampaignBySpecId(campaignSpecId),
    enabled: !!campaignSpecId,
  })
}

export function useGetOrCreateCampaign() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (campaignSpecId: string) => apiClient.getOrCreateCampaignFromSpec(campaignSpecId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGNS_QUERY_KEY] })
    },
  })
}
