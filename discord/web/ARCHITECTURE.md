# Frontend 架構文件

## 專案概述

本專案採用 **功能模組化架構 (Feature-based Architecture)**，使用 Vite + React + TypeScript 開發。

## 技術棧

- **構建工具**: Vite 7.x
- **框架**: React 19.x
- **語言**: TypeScript 5.x
- **路由**: React Router DOM 7.x
- **狀態管理**: TanStack Query (React Query) 5.x
- **HTTP 客戶端**: Axios 1.x
- **樣式**: Tailwind CSS 4.x
- **代碼規範**: ESLint + Prettier

## 目錄結構

```
src/
├── features/                    # 功能模組（核心）
│   ├── line/                    # Line 功能模組
│   │   ├── components/          # 該功能專屬組件
│   │   ├── hooks/               # 該功能專屬 Hooks
│   │   ├── services/            # API 服務
│   │   ├── types/               # 類型定義
│   │   ├── routes.tsx           # 該功能的路由配置
│   │   └── index.ts             # 功能模組統一導出
│   │
│   ├── dealer/                  # Dealer 功能模組
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── routes.tsx
│   │   └── index.ts
│   │
│   └── [其他功能模組]/
│
├── shared/                      # 共用資源
│   ├── components/              # 共用 UI 組件
│   │   ├── ui/                  # 基礎 UI 組件（Button, Input, Modal...）
│   │   ├── layout/              # 佈局組件（Header, Sidebar, Footer）
│   │   └── index.ts
│   │
│   ├── hooks/                   # 共用 Hooks
│   │   ├── useLocalStorage.ts
│   │   ├── useDebounce.ts
│   │   └── index.ts
│   │
│   ├── utils/                   # 共用工具函數
│   │   ├── format.ts
│   │   ├── validation.ts
│   │   └── index.ts
│   │
│   ├── types/                   # 共用類型定義
│   │   ├── api.types.ts
│   │   ├── common.types.ts
│   │   └── index.ts
│   │
│   └── config/                  # 配置檔案
│       ├── api.config.ts
│       └── index.ts
│
├── core/                        # 核心功能
│   ├── api/                     # API 核心
│   │   ├── client.ts            # API 客戶端
│   │   └── index.ts
│   │
│   └── router/                  # 路由核心
│       ├── routes.tsx           # 路由配置
│       └── index.ts
│
├── assets/                      # 靜態資源
│   ├── images/
│   ├── icons/
│   └── styles/
│
├── App.tsx                      # 根組件
├── main.tsx                     # 入口檔案
└── vite-env.d.ts               # Vite 類型定義
```

## 架構原則

### 1. 功能模組獨立性
每個功能模組（Feature）應該是高內聚、低耦合的單元：
- 包含該功能所需的所有資源（components, hooks, services, types）
- 通過 `index.ts` 統一導出公開接口
- 避免直接引用其他功能模組的內部實現
- 只依賴 `shared` 和 `core` 層的資源

### 2. 共用資源管理
`shared` 目錄存放跨功能模組的共用資源：
- **UI 組件**: 可在多個功能中重複使用的純展示組件
- **Hooks**: 通用的業務邏輯或狀態管理
- **Utils**: 工具函數和輔助方法
- **Types**: 共用的類型定義

### 3. 核心層職責
`core` 目錄提供應用程式的基礎設施：
- **API**: 統一的 API 客戶端配置
- **Router**: 路由配置和管理
- **Providers**: 全域的 Context Providers（如需要）

### 4. 命名規範
- **檔案命名**: 使用 PascalCase（組件）或 camelCase（工具函數）
- **組件**: `ComponentName.tsx`
- **Hooks**: `useHookName.ts`
- **Services**: `serviceName.service.ts` 或 `serviceName.ts`
- **Types**: `typeName.types.ts`

### 5. 導入路徑
使用路徑別名簡化導入：
```typescript
// ✅ 推薦
import { Button } from '@/shared/components/ui'
import { useProjects } from '@/features/project'

// ❌ 避免
import { Button } from '../../../shared/components/ui/Button'
```

## 功能模組範例

### 基本結構
每個功能模組遵循以下結構：

```typescript
// features/example/index.ts
export { ExampleList, ExampleForm } from './components'
export { useExample, useExamples } from './hooks'
export { exampleService } from './services'
export type { Example, CreateExampleDto } from './types'
export { exampleRoutes } from './routes'
```

### 類型定義
```typescript
// features/example/types/example.types.ts
export interface Example {
  id: string
  name: string
  createdAt: string
}

export interface CreateExampleDto {
  name: string
}
```

### 服務層
```typescript
// features/example/services/exampleService.ts
import { apiClient } from '@/core/api'
import type { Example } from '../types'

// 定義回傳型別（Data 必定是 object）
interface ExampleListResponse {
  items: Example[]
  total: number
}

export const exampleService = {
  async getAll(): Promise<Example[]> {
    // apiClient 會自動提取 Data 欄位
    const result = await apiClient.get<ExampleListResponse>('/project_tracker/api/example')
    return result.items
  },
  
  async getById(id: string): Promise<Example> {
    return await apiClient.get<Example>(`/project_tracker/api/example/${id}`)
  }
}
```

### 自定義 Hook
```typescript
// features/example/hooks/useExamples.ts
import { useQuery } from '@tanstack/react-query'
import { ApiError } from '@/core/api'
import { exampleService } from '../services'

export function useExamples() {
  const { data = [], isLoading: loading, error } = useQuery({
    queryKey: ['examples'],
    queryFn: () => exampleService.getAll(),
  })

  return { 
    data, 
    loading, 
    error: error instanceof ApiError ? error.errorMessage : null 
  }
}
```

### 路由配置
```typescript
// features/example/routes.tsx
import { RouteObject } from 'react-router-dom'
import { ExampleList } from './components'

export const exampleRoutes: RouteObject[] = [
  {
    path: 'examples',
    element: <ExampleList />
  }
]
```

## 開發流程

### 新增功能模組
1. 在 `features/` 下創建新目錄
2. 按需創建子目錄（components, hooks, services, types）
3. 創建 `index.ts` 統一導出
4. 在 `core/router/routes.tsx` 中註冊路由

### 新增共用組件
1. 在 `shared/components/` 下創建組件目錄
2. 實現組件邏輯
3. 在上層 `index.ts` 中導出
4. 在需要的地方使用路徑別名導入

### API 整合
1. **配置 API 客戶端**: 已在 `core/api/client.ts` 配置，自動處理統一回傳格式
2. **定義服務層**: 在功能模組的 `services/` 中使用 `apiClient` 調用 API
3. **創建 Query Hooks**: 使用 TanStack Query 封裝數據獲取邏輯
4. **使用 Mutation Hooks**: 處理創建、更新、刪除操作並自動刷新緩存

**統一回傳格式**:
```typescript
// 後端回傳格式
{
  "Data": {"items": [...], "total": 10},
  "ErrorCode": 0,
  "ErrorMessage": null
}

// apiClient 自動提取 Data，前端收到
{ items: [...], total: 10 }
```

**範例流程**:
```typescript
// 1. Service 層調用 API（apiClient 自動提取 Data）
const result = await apiClient.get('/project_tracker/api/example')
return result.items

// 2. Hook 層使用 React Query
const { data } = useQuery({
  queryKey: ['examples'],
  queryFn: () => exampleService.getAll()
})

// 3. 組件使用 Hook
const { data, loading, error } = useExamples()
```

## 構建與部署

### 構建配置
專案構建後會輸出到後端靜態目錄：
```javascript
// vite.config.ts
export default defineConfig({
  base: '/kitchen/',
  build: {
    outDir: '../backend/project_tracker/static/dist',
    emptyOutDir: true
  }
})
```

### 路由配置
確保前端路由的 basename 與後端路由匹配：
```typescript
// main.tsx
<BrowserRouter basename="/kitchen">
  <App />
</BrowserRouter>
```

## 最佳實踐

1. **保持模組獨立**: 避免功能模組之間的直接依賴
2. **類型優先**: 先定義類型，再實現邏輯
3. **統一導出**: 使用 `index.ts` 管理導出
4. **代碼復用**: 將可復用的邏輯提取到 `shared` 或自定義 Hook
5. **一致性**: 遵循統一的命名和組織規範
6. **文檔化**: 為複雜邏輯添加註釋

## 數據管理

### TanStack Query (React Query)
專案已整合 TanStack Query 用於伺服器狀態管理：

**優勢**:
- 自動緩存和背景更新
- 載入和錯誤狀態管理
- 自動重試和請求去重
- 分頁和無限滾動支援

**配置** (`App.tsx`):
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 分鐘
    },
  },
})
```

### Axios HTTP 客戶端
統一的 HTTP 請求客戶端 (`core/api/client.ts`):

**功能**:
- 請求/響應攔截器
- 自動添加認證 token
- 統一錯誤處理
- 請求超時設置

### 其他狀態管理
如需全域客戶端狀態管理，推薦：
- **Zustand**: 輕量、簡單、TypeScript 友好
- **Redux Toolkit**: 適合大型複雜應用

### UI 庫
可整合：
- **shadcn/ui**: 可自定義的組件庫
- **Ant Design**: 企業級 UI 組件庫
- **Material-UI**: Google Material Design 實現

### 表單處理
推薦：
- **React Hook Form**: 高性能表單處理
- **Zod**: TypeScript-first 的數據驗證

## 參考資源

- [Vite 官方文檔](https://vitejs.dev/)
- [React 官方文檔](https://react.dev/)
- [TypeScript 官方文檔](https://www.typescriptlang.org/)
- [React Router 官方文檔](https://reactrouter.com/)

---

**維護日期**: 2026-01-21  
**版本**: 1.1.0
