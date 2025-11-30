import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { AssetCreate, AssetUpdate, AssetListParams } from '../types'

export const ASSETS_QUERY_KEY = 'assets'

export function useAssets(params?: AssetListParams) {
  return useQuery({
    queryKey: [ASSETS_QUERY_KEY, params],
    queryFn: () => apiClient.getAssets(params),
  })
}

export function useAsset(assetId: string) {
  return useQuery({
    queryKey: [ASSETS_QUERY_KEY, assetId],
    queryFn: () => apiClient.getAsset(assetId),
    enabled: !!assetId,
  })
}

export function useCreateAsset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: AssetCreate) => apiClient.createAsset(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ASSETS_QUERY_KEY] })
    },
  })
}

export function useUpdateAsset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ assetId, data }: { assetId: string; data: AssetUpdate }) =>
      apiClient.updateAsset(assetId, data),
    onSuccess: (updatedAsset) => {
      queryClient.invalidateQueries({ queryKey: [ASSETS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [ASSETS_QUERY_KEY, updatedAsset.id] })
    },
  })
}

export function useDeleteAsset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (assetId: string) => apiClient.deleteAsset(assetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ASSETS_QUERY_KEY] })
    },
  })
}

export function useUploadAsset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (formData: FormData) => apiClient.uploadAsset(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ASSETS_QUERY_KEY] })
    },
  })
}
