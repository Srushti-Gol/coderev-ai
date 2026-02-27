import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { repositoriesApi } from '../api/repositories'

export function useRepositories(params?: { search?: string }) {
  return useQuery({
    queryKey: ['repositories', params],
    queryFn: () => repositoriesApi.list(params),
  })
}

export function useRepository(id: number) {
  return useQuery({
    queryKey: ['repositories', id],
    queryFn: () => repositoriesApi.get(id),
    enabled: !!id,
  })
}

export function useSyncRepositories() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: repositoriesApi.sync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    },
  })
}

export function useActivateRepository() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => repositoriesApi.activate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    },
  })
}

export function useDeactivateRepository() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => repositoriesApi.deactivate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    },
  })
}
