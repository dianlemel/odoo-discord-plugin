import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/core/api'
import { lineService } from '../services'
import type { CreateLineDto, UpdateLineDto } from '../types'

// 查詢所有 Line
export function useLines() {
  const {
    data = [],
    isLoading: loading,
    error,
  } = useQuery({
    queryKey: ['lines'],
    queryFn: () => lineService.getAll(),
  })

  return {
    data,
    loading,
    error: error instanceof ApiError ? error.errorMessage : null,
  }
}

// 查詢單一 Line
export function useLine(id: string) {
  const {
    data = null,
    isLoading: loading,
    error,
  } = useQuery({
    queryKey: ['lines', id],
    queryFn: () => lineService.getById(id),
    enabled: !!id,
  })

  return {
    data,
    loading,
    error: error instanceof ApiError ? error.errorMessage : null,
  }
}

// 創建 Line
export function useCreateLine() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateLineDto) => lineService.create(data),
    onSuccess: () => {
      // 刷新列表
      queryClient.invalidateQueries({ queryKey: ['lines'] })
    },
  })
}

// 更新 Line
export function useUpdateLine() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateLineDto) => lineService.update(data),
    onSuccess: (_, variables) => {
      // 刷新列表和詳情
      queryClient.invalidateQueries({ queryKey: ['lines'] })
      queryClient.invalidateQueries({ queryKey: ['lines', variables.id] })
    },
  })
}

// 刪除 Line
export function useDeleteLine() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => lineService.delete(id),
    onSuccess: () => {
      // 刷新列表
      queryClient.invalidateQueries({ queryKey: ['lines'] })
    },
  })
}
