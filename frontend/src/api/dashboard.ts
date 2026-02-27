import apiClient from './client'
import {
  DashboardStats,
  PRVelocityData,
  CycleTimeData,
  DebtScoreData,
  QualityTrendData,
  PRSizeDistribution,
  WeeklyDigest,
} from '../types'

export const dashboardApi = {
  getStats: async (days?: number): Promise<DashboardStats> => {
    const { data } = await apiClient.get<DashboardStats>('/api/dashboard/stats', {
      params: { days },
    })
    return data
  },

  getPRVelocity: async (days?: number): Promise<PRVelocityData[]> => {
    const { data } = await apiClient.get<PRVelocityData[]>('/api/dashboard/pr-velocity', {
      params: { days },
    })
    return data
  },

  getCycleTime: async (days?: number): Promise<CycleTimeData[]> => {
    const { data } = await apiClient.get<CycleTimeData[]>('/api/dashboard/cycle-time', {
      params: { days },
    })
    return data
  },

  getDebtScore: async (repoId?: number): Promise<DebtScoreData[]> => {
    const { data } = await apiClient.get<DebtScoreData[]>('/api/dashboard/debt-score', {
      params: { repo_id: repoId },
    })
    return data
  },

  getQualityOverTime: async (days?: number): Promise<QualityTrendData[]> => {
    const { data } = await apiClient.get<QualityTrendData[]>('/api/dashboard/quality-over-time', {
      params: { days },
    })
    return data
  },

  getPRSizeDistribution: async (days?: number): Promise<PRSizeDistribution[]> => {
    const { data } = await apiClient.get<PRSizeDistribution[]>(
      '/api/dashboard/pr-size-distribution',
      { params: { days } }
    )
    return data
  },

  getWeeklyDigest: async (): Promise<WeeklyDigest> => {
    const { data } = await apiClient.get<WeeklyDigest>('/api/dashboard/weekly-digest')
    return data
  },
}
