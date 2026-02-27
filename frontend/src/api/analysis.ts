import apiClient from './client'
import { Analysis, AnalysisSummary } from '../types'

export const analysisApi = {
  getPRAnalyses: async (
    prId: number,
    params?: { analysis_type?: string; severity?: string; skip?: number; limit?: number }
  ): Promise<Analysis[]> => {
    const { data } = await apiClient.get<Analysis[]>(`/api/analysis/pr/${prId}`, { params })
    return data
  },

  getPRSummary: async (prId: number): Promise<AnalysisSummary> => {
    const { data } = await apiClient.get<AnalysisSummary>(`/api/analysis/pr/${prId}/summary`)
    return data
  },

  dismiss: async (id: number): Promise<{ message: string }> => {
    const { data } = await apiClient.patch(`/api/analysis/${id}/dismiss`)
    return data
  },

  verify: async (id: number): Promise<{ message: string }> => {
    const { data } = await apiClient.patch(`/api/analysis/${id}/verify`)
    return data
  },
}
