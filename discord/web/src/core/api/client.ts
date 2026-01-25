import axios, { AxiosError } from 'axios'

// API 統一回傳格式（Data 必定是 object）
export interface ApiResponse<T extends Record<string, any> = Record<string, any>> {
  Data: T // 必定是 object，不會是 null
  ErrorCode: number
  ErrorMessage: string | null
}

// API 錯誤類別
export class ApiError extends Error {
  errorCode: number
  errorMessage: string
  httpStatus?: number

  constructor(errorCode: number, errorMessage: string, httpStatus?: number) {
    super(errorMessage)
    this.name = 'ApiError'
    this.errorCode = errorCode
    this.errorMessage = errorMessage
    this.httpStatus = httpStatus
  }
}

// 創建 axios 實例
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/project-tracker/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 請求攔截器
apiClient.interceptors.request.use(
  config => {
    // 從 localStorage 獲取 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 響應攔截器
apiClient.interceptors.response.use(
  response => {
    const data: ApiResponse = response.data

    // 檢查業務邏輯錯誤碼
    if (data.ErrorCode !== 0) {
      // ErrorCode 不為 0，視為業務錯誤
      throw new ApiError(data.ErrorCode, data.ErrorMessage || '未知錯誤', response.status)
    }

    // 成功，直接返回 Data
    return data.Data as any
  },
  (error: AxiosError<ApiResponse>) => {
    // HTTP 錯誤或網路錯誤
    if (error.response) {
      // 有收到伺服器回應
      const data = error.response.data

      // 如果有標準格式的錯誤回應
      if (data && 'ErrorCode' in data && 'ErrorMessage' in data) {
        const apiError = new ApiError(
          data.ErrorCode,
          data.ErrorMessage || '請求失敗',
          error.response.status
        )

        // 根據 HTTP 狀態碼做特殊處理
        if (error.response.status === 401) {
          // 未授權，清除 token
          localStorage.removeItem('token')
          console.error('未授權，請重新登入')
        } else if (error.response.status === 403) {
          console.error('權限不足')
        }

        return Promise.reject(apiError)
      }

      // 非標準格式的錯誤回應
      return Promise.reject(
        new ApiError(
          error.response.status,
          `HTTP ${error.response.status}: ${error.message}`,
          error.response.status
        )
      )
    }

    // 網路錯誤或請求超時
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new ApiError(0, '請求超時'))
    }

    return Promise.reject(new ApiError(0, error.message || '網路連線失敗'))
  }
)
