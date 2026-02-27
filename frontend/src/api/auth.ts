import apiClient from './client'
import { User } from '../types'

export const authApi = {
  getMe: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/auth/me')
    return data
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout')
  },

  getGithubLoginUrl: (): string => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    return `${apiUrl}/auth/github`
  },
}
