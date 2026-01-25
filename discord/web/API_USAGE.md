# API 使用指南

本文件說明如何在專案中使用統一的 API 回傳格式與 TanStack Query 進行 API 調用。

## 📦 已安裝的套件

- **axios**: ^1.13.2 - HTTP 客戶端
- **@tanstack/react-query**: ^5.90.19 - 伺服器狀態管理

## 📋 統一回傳格式

後端所有 API 都使用以下統一格式：

```typescript
interface ApiResponse<T> {
  Data: T              // 必定是 object
  ErrorCode: number    // 0 表示成功
  ErrorMessage: string | null
}
```

### 成功回應範例
```json
{
  "Data": {"id": 1, "name": "test"},
  "ErrorCode": 0,
  "ErrorMessage": null
}
```

### 錯誤回應範例
```json
{
  "Data": {},
  "ErrorCode": 402,
  "ErrorMessage": "缺少必要參數"
}
```

## 🔧 配置

### API Client

已在 `src/core/api/client.ts` 配置好，會自動處理統一格式：

```typescript
import { apiClient, ApiError } from '@/core/api'

// 基礎配置
- baseURL: '/project-tracker/api'
- timeout: 10秒
- 自動提取 Data 欄位
- 自動處理錯誤（ApiError）
- 自動添加 JWT token (從 localStorage)
```

### React Query

已在 `App.tsx` 配置 QueryClientProvider：

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,                    // 失敗重試 1 次
      refetchOnWindowFocus: false, // 不自動重新獲取
      staleTime: 5 * 60 * 1000,   // 緩存 5 分鐘
    },
  },
})
```

## 📝 使用方式

### 1. 定義服務層

在功能模組的 `services/` 目錄中定義 API 服務：

```typescript
// features/example/services/exampleService.ts
import { apiClient } from '@/core/api'
import type { Example, CreateExampleDto } from '../types'

// 定義回傳型別（Data 必定是 object）
interface ExampleListResponse {
  items: Example[]
  total: number
}

export const exampleService = {
  // GET /project_tracker/api/example
  // 後端回傳: { "Data": {"items": [...], "total": 10}, "ErrorCode": 0, "ErrorMessage": null }
  // apiClient 自動提取 Data: { items: [...], total: 10 }
  async getAll(): Promise<Example[]> {
    const result = await apiClient.get<ExampleListResponse>('/example')
    return result.items
  },

  // GET /project_tracker/api/example/:id
  // 後端回傳: { "Data": {"id": 1, "name": "..."}, "ErrorCode": 0, "ErrorMessage": null }
  // apiClient 自動提取 Data: { id: 1, name: "..." }
  async getById(id: string): Promise<Example> {
    return await apiClient.get<Example>(`/example/${id}`)
  },

  // POST /project_tracker/api/example
  async create(data: CreateExampleDto): Promise<Example> {
    return await apiClient.post<Example>('/example', data)
  },

  // PUT /project_tracker/api/example/:id
  async update(id: string, data: Partial<CreateExampleDto>): Promise<Example> {
    return await apiClient.put<Example>(`/example/${id}`, data)
  },

  // DELETE /project_tracker/api/example/:id
  async delete(id: string): Promise<void> {
    await apiClient.delete<{ deleted: boolean }>(`/example/${id}`)
  },
}
```

### 2. 創建 Query Hooks

在功能模組的 `hooks/` 目錄中使用 React Query：

```typescript
// features/example/hooks/useExamples.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/core/api'
import { exampleService } from '../services'
import type { CreateExampleDto } from '../types'

// 查詢列表
export function useExamples() {
  const { data = [], isLoading: loading, error } = useQuery({
    queryKey: ['examples'],
    queryFn: () => exampleService.getAll(),
  })

  return {
    data,
    loading,
    error: error instanceof ApiError ? error.errorMessage : null,
  }
}

// 查詢單一項目
export function useExample(id: string) {
  const { data = null, isLoading: loading, error } = useQuery({
    queryKey: ['examples', id],
    queryFn: () => exampleService.getById(id),
    enabled: !!id, // 只有在 id 存在時才執行
  })

  return {
    data,
    loading,
    error: error instanceof ApiError ? error.errorMessage : null,
  }
}

// 創建
export function useCreateExample() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateExampleDto) => exampleService.create(data),
    onSuccess: () => {
      // 創建成功後刷新列表
      queryClient.invalidateQueries({ queryKey: ['examples'] })
    },
  })
}

// 更新
export function useUpdateExample() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateExampleDto> }) =>
      exampleService.update(id, data),
    onSuccess: (_, variables) => {
      // 更新成功後刷新列表和詳情
      queryClient.invalidateQueries({ queryKey: ['examples'] })
      queryClient.invalidateQueries({ queryKey: ['examples', variables.id] })
    },
  })
}

// 刪除
export function useDeleteExample() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => exampleService.delete(id),
    onSuccess: () => {
      // 刪除成功後刷新列表
      queryClient.invalidateQueries({ queryKey: ['examples'] })
    },
  })
}
```

### 3. 在組件中使用

```typescript
// features/example/components/ExampleList.tsx
import { useExamples, useCreateExample, useDeleteExample } from '../hooks'
import { ApiError } from '@/core/api'

export function ExampleList() {
  const { data, loading, error } = useExamples()
  const createExample = useCreateExample()
  const deleteExample = useDeleteExample()

  const handleCreate = async () => {
    try {
      await createExample.mutateAsync({ name: '新項目' })
      alert('創建成功！')
    } catch (error) {
      if (error instanceof ApiError) {
        // 根據錯誤碼做不同處理
        if (error.errorCode === 402) {
          alert('缺少必要參數')
        } else {
          alert(error.errorMessage)
        }
      }
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteExample.mutateAsync(id)
      alert('刪除成功！')
    } catch (error) {
      if (error instanceof ApiError) {
        alert(`刪除失敗: ${error.errorMessage}`)
      }
    }
  }

  if (loading) return <div>載入中...</div>
  if (error) return <div>錯誤：{error}</div>

  return (
    <div>
      <button onClick={handleCreate}>新增</button>
      {data.map((item) => (
        <div key={item.id}>
          {item.name}
          <button onClick={() => handleDelete(item.id)}>刪除</button>
        </div>
      ))}
    </div>
  )
}
```

## 🎯 最佳實踐

### 1. Query Keys 規範

```typescript
// ✅ 好的做法
['examples']              // 列表
['examples', id]          // 單一項目
['examples', { filter }]  // 帶篩選的列表
['examples', id, 'comments'] // 關聯資源

// ❌ 避免
['getExamples']           // 不要包含動詞
['example-list']          // 使用陣列而不是字串
```

### 2. 錯誤處理

```typescript
import { ApiError } from '@/core/api'

// 在組件中處理錯誤
const { data, error } = useExamples()

if (error) {
  return <ErrorMessage error={error} />
}

// 在 mutation 中處理錯誤
const createExample = useCreateExample()

const handleCreate = async () => {
  try {
    await createExample.mutateAsync(data)
  } catch (error) {
    if (error instanceof ApiError) {
      // 根據錯誤碼處理
      if (error.errorCode === 402) {
        alert('缺少必要參數')
      } else if (error.errorCode === 407) {
        alert('資料重複')
      } else if (error.errorCode === 500) {
        alert('伺服器錯誤')
      } else {
        alert(error.errorMessage)
      }
    }
  }
}
```

### 常用錯誤碼

```typescript
// 通用錯誤（400-499）
400  // 請求格式錯誤
401  // 無效的 JSON 格式
402  // 缺少必要參數
403  // 參數格式錯誤
404  // 未授權
407  // 資料重複

// 伺服器錯誤（500-599）
500  // 內部錯誤
501  // 資料庫錯誤

// 業務邏輯錯誤（1000+）
1001 // 專案不存在
1002 // 專案已存在
2001 // 使用者不存在
```

### 3. 載入狀態

```typescript
const { data, isLoading, isFetching } = useExamples()

// isLoading: 第一次載入
// isFetching: 背景重新獲取

if (isLoading) return <Spinner />

return (
  <div>
    {isFetching && <LoadingBar />}
    {/* 內容 */}
  </div>
)
```

### 4. 樂觀更新

```typescript
export function useUpdateExample() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }) => exampleService.update(id, data),
    // 樂觀更新
    onMutate: async (variables) => {
      // 取消正在進行的查詢
      await queryClient.cancelQueries({ queryKey: ['examples', variables.id] })

      // 獲取舊數據
      const previousData = queryClient.getQueryData(['examples', variables.id])

      // 樂觀更新
      queryClient.setQueryData(['examples', variables.id], variables.data)

      return { previousData }
    },
    // 錯誤時回滾
    onError: (err, variables, context) => {
      queryClient.setQueryData(
        ['examples', variables.id],
        context.previousData
      )
    },
    // 成功後刷新
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['examples'] })
    },
  })
}
```

## 🔍 除錯

### 安裝 React Query DevTools (可選)

```bash
npm install @tanstack/react-query-devtools
```

```typescript
// App.tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

<QueryClientProvider client={queryClient}>
  <App />
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

## ⚠️ 重要注意事項

### 1. Data 必定是 Object
後端的 `Data` 欄位必定是 object，不會是 null、string、number 或 array。

```typescript
// ✅ 正確
interface UserResponse {
  id: number
  name: string
}

// ✅ 列表應該包裝在 object 中
interface UserListResponse {
  items: User[]
  total: number
}

// ❌ 錯誤：不應該直接是陣列
type UserListResponse = User[]
```

### 2. apiClient 自動提取 Data
不需要手動存取 `.data`：

```typescript
// ❌ 錯誤
const response = await apiClient.get('/api/resource')
const data = response.data  // 不需要這樣

// ✅ 正確
const data = await apiClient.get('/api/resource')  // 已經是 Data 的內容
```

### 3. 使用 ApiError 處理錯誤
統一使用 `ApiError` 來處理後端錯誤：

```typescript
import { ApiError } from '@/core/api'

try {
  await apiClient.get('/api/resource')
} catch (error) {
  if (error instanceof ApiError) {
    console.log(error.errorCode)     // ErrorCode
    console.log(error.errorMessage)  // ErrorMessage
    console.log(error.httpStatus)    // HTTP 狀態碼
  }
}
```

## 📚 參考資源

- [TanStack Query 官方文檔](https://tanstack.com/query/latest)
- [Axios 官方文檔](https://axios-http.com/)
- [React Query 最佳實踐](https://tkdodo.eu/blog/practical-react-query)

---

**更新日期**: 2026-01-21
