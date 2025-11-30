import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { CampaignSpecCreate, CampaignSpecUpdate, PaginationParams } from '../types'
import { ASSETS_QUERY_KEY } from './useAssets'
import { TARGET_GROUPS_QUERY_KEY } from './useTargetGroups'

export const CAMPAIGN_SPECS_QUERY_KEY = 'campaign-specs'

export function useCampaignSpecs(params?: PaginationParams) {
  return useQuery({
    queryKey: [CAMPAIGN_SPECS_QUERY_KEY, params],
    queryFn: () => apiClient.getCampaignSpecs(params),
  })
}

export function useCampaignSpec(id: string) {
  return useQuery({
    queryKey: [CAMPAIGN_SPECS_QUERY_KEY, id],
    queryFn: () => apiClient.getCampaignSpec(id),
    enabled: !!id,
  })
}

export function useCreateCampaignSpec() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CampaignSpecCreate) => apiClient.createCampaignSpec(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGN_SPECS_QUERY_KEY] })
    },
  })
}

export function useUpdateCampaignSpec() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CampaignSpecUpdate }) =>
      apiClient.updateCampaignSpec(id, data),
    onSuccess: (updatedCampaignSpec) => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGN_SPECS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [CAMPAIGN_SPECS_QUERY_KEY, updatedCampaignSpec.id] })
    },
  })
}

export function useDeleteCampaignSpec() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.deleteCampaignSpec(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGN_SPECS_QUERY_KEY] })
    },
  })
}

// Campaign Spec Assets
export function useCampaignSpecAssets(id: string) {
  return useQuery({
    queryKey: [CAMPAIGN_SPECS_QUERY_KEY, id, ASSETS_QUERY_KEY],
    queryFn: () => apiClient.getCampaignSpecAssets(id),
    enabled: !!id,
  })
}

export function useAddCampaignSpecAsset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, assetId }: { id: string; assetId: string }) =>
      apiClient.addCampaignSpecAsset(id, assetId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGN_SPECS_QUERY_KEY, variables.id, ASSETS_QUERY_KEY] })
    },
  })
}

export function useRemoveCampaignSpecAsset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, assetId }: { id: string; assetId: string }) =>
      apiClient.removeCampaignSpecAsset(id, assetId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGN_SPECS_QUERY_KEY, variables.id, ASSETS_QUERY_KEY] })
    },
  })
}

// Campaign Spec Target Groups
export function useCampaignSpecTargetGroups(id: string) {
  return useQuery({
    queryKey: [CAMPAIGN_SPECS_QUERY_KEY, id, TARGET_GROUPS_QUERY_KEY],
    queryFn: () => apiClient.getCampaignSpecTargetGroups(id),
    enabled: !!id,
  })
}

export function useAddCampaignSpecTargetGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, targetGroupId }: { id: string; targetGroupId: string }) =>
      apiClient.addCampaignSpecTargetGroup(id, targetGroupId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGN_SPECS_QUERY_KEY, variables.id, TARGET_GROUPS_QUERY_KEY] })
    },
  })
}

export function useRemoveCampaignSpecTargetGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, targetGroupId }: { id: string; targetGroupId: string }) =>
      apiClient.removeCampaignSpecTargetGroup(id, targetGroupId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGN_SPECS_QUERY_KEY, variables.id, TARGET_GROUPS_QUERY_KEY] })
    },
  })
}
