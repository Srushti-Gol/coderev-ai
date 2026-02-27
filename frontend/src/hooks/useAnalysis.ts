import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { analysisApi } from '../api/analysis'

export function useAnalysis(prId: number, params?: { analysis_type?: string; severity?: string }) {
  return useQuery({
    queryKey: ['analysis', prId, params],
    queryFn: () => analysisApi.getPRAnalyses(prId, params),
    enabled: !!prId,
  })
}

export function useAnalysisSummary(prId: number) {
  return useQuery({
    queryKey: ['analysis-summary', prId],
    queryFn: () => analysisApi.getPRSummary(prId),
    enabled: !!prId,
  })
}

export function useDismissAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => analysisApi.dismiss(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis'] })
      queryClient.invalidateQueries({ queryKey: ['analysis-summary'] })
    },
  })
}

export function useVerifyAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => analysisApi.verify(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis'] })
    },
  })
}
