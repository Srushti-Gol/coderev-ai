import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export function useAuth() {
  const { token, user, setUser, logout } = useAuthStore()

  const { data, error, isLoading } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authApi.getMe,
    enabled: !!token,
    retry: 1,
  })

  useEffect(() => {
    if (data) {
      setUser(data)
    }
  }, [data, setUser])

  useEffect(() => {
    if (error) {
      logout()
    }
  }, [error, logout])

  return {
    user: data || user,
    isLoading,
    isAuthenticated: !!token,
    logout,
  }
}
