import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/core/api'
import { dealerService } from '../services'
import type { CreateDealerDto, UpdateDealerDto } from '../types'

// 查詢所有經銷商
export function useDealers() {
  const {
    data = [],
    isLoading: loading,
    error,
  } = useQuery({
    queryKey: ['dealers'],
    queryFn: () => dealerService.getAll(),
  })

  return {
    data,
    loading,
    error: error instanceof ApiError ? error.errorMessage : null,
  }
}

// 查詢單一經銷商
export function useDealer(id: string) {
  const {
    data = null,
    isLoading: loading,
    error,
  } = useQuery({
    queryKey: ['dealers', id],
    queryFn: () => dealerService.getById(id),
    enabled: !!id,
  })

  return {
    data,
    loading,
    error: error instanceof ApiError ? error.errorMessage : null,
  }
}

// 創建經銷商
export function useCreateDealer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateDealerDto) => dealerService.create(data),
    onSuccess: () => {
      // 刷新列表
      queryClient.invalidateQueries({ queryKey: ['dealers'] })
    },
  })
}

// 更新經銷商
export function useUpdateDealer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateDealerDto) => dealerService.update(data),
    onSuccess: (_, variables) => {
      // 刷新列表和詳情
      queryClient.invalidateQueries({ queryKey: ['dealers'] })
      queryClient.invalidateQueries({ queryKey: ['dealers', variables.id] })
    },
  })
}

// 刪除經銷商
export function useDeleteDealer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => dealerService.delete(id),
    onSuccess: () => {
      // 刷新列表
      queryClient.invalidateQueries({ queryKey: ['dealers'] })
    },
  })
}
