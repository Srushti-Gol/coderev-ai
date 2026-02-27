import apiClient from './client'
import { Repository } from '../types'

export const repositoriesApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string }): Promise<Repository[]> => {
    const { data } = await apiClient.get<Repository[]>('/api/repositories/', { params })
    return data
  },

  get: async (id: number): Promise<Repository> => {
    const { data } = await apiClient.get<Repository>(`/api/repositories/${id}`)
    return data
  },

  sync: async (): Promise<Repository[]> => {
    const { data } = await apiClient.post<Repository[]>('/api/repositories/sync')
    return data
  },

  activate: async (id: number): Promise<{ message: string; webhook_id?: number }> => {
    const { data } = await apiClient.post(`/api/repositories/${id}/activate`)
    return data
  },

  deactivate: async (id: number): Promise<{ message: string }> => {
    const { data } = await apiClient.post(`/api/repositories/${id}/deactivate`)
    return data
  },

  delete: async (id: number): Promise<{ message: string }> => {
    const { data } = await apiClient.delete(`/api/repositories/${id}`)
    return data
  },
}
