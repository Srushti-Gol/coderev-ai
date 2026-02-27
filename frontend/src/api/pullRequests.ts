import apiClient from './client'
import { PullRequest } from '../types'

export const pullRequestsApi = {
  list: async (params?: {
    repo_id?: number
    status?: string
    ai_status?: string
    skip?: number
    limit?: number
  }): Promise<PullRequest[]> => {
    const { data } = await apiClient.get<PullRequest[]>('/api/pull-requests/', { params })
    return data
  },

  get: async (id: number): Promise<PullRequest> => {
    const { data } = await apiClient.get<PullRequest>(`/api/pull-requests/${id}`)
    return data
  },

  triggerAnalysis: async (id: number): Promise<{ message: string; task_id: string | null }> => {
    const { data } = await apiClient.post(`/api/pull-requests/${id}/analyze`)
    return data
  },

  sync: async (id: number): Promise<PullRequest> => {
    const { data } = await apiClient.get<PullRequest>(`/api/pull-requests/${id}/sync`)
    return data
  },
}
