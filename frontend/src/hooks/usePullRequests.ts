import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { pullRequestsApi } from '../api/pullRequests'

export function usePullRequests(params?: {
  repo_id?: number
  status?: string
  ai_status?: string
}) {
  return useQuery({
    queryKey: ['pull-requests', params],
    queryFn: () => pullRequestsApi.list(params),
  })
}

export function usePullRequest(id: number) {
  return useQuery({
    queryKey: ['pull-requests', id],
    queryFn: () => pullRequestsApi.get(id),
    enabled: !!id,
    refetchInterval: (data) => {
      // Poll while analyzing
      if (data?.ai_status === 'analyzing') return 5000
      return false
    },
  })
}

export function useTriggerAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => pullRequestsApi.triggerAnalysis(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['pull-requests', id] })
      queryClient.invalidateQueries({ queryKey: ['pull-requests'] })
    },
  })
}
