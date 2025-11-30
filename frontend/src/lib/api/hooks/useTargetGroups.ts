import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { TargetGroupCreate, TargetGroupUpdate, PaginationParams } from '../types'

export const TARGET_GROUPS_QUERY_KEY = 'target-groups'

export function useTargetGroups(params?: PaginationParams) {
  return useQuery({
    queryKey: [TARGET_GROUPS_QUERY_KEY, params],
    queryFn: () => apiClient.getTargetGroups(params),
  })
}

export function useTargetGroup(targetGroupId: string) {
  return useQuery({
    queryKey: [TARGET_GROUPS_QUERY_KEY, targetGroupId],
    queryFn: () => apiClient.getTargetGroup(targetGroupId),
    enabled: !!targetGroupId,
  })
}

export function useCreateTargetGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: TargetGroupCreate) => apiClient.createTargetGroup(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TARGET_GROUPS_QUERY_KEY] })
    },
  })
}

export function useUpdateTargetGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ targetGroupId, data }: { targetGroupId: string; data: TargetGroupUpdate }) =>
      apiClient.updateTargetGroup(targetGroupId, data),
    onSuccess: (updatedTargetGroup) => {
      queryClient.invalidateQueries({ queryKey: [TARGET_GROUPS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [TARGET_GROUPS_QUERY_KEY, updatedTargetGroup.id] })
    },
  })
}

export function useDeleteTargetGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (targetGroupId: string) => apiClient.deleteTargetGroup(targetGroupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TARGET_GROUPS_QUERY_KEY] })
    },
  })
}
