import type { Line, CreateLineDto, UpdateLineDto } from '../types'
// import { apiClient, ApiError } from '@/core/api'

export const lineService = {
  async getAll(): Promise<Line[]> {
    // 實際使用 API 時的寫法：
    // const result = await apiClient.get<{ items: Line[]; total: number }>('/lines')
    // return result.items
    //
    // 說明：apiClient 會自動提取後端回傳的 Data 欄位
    // 後端格式: { "Data": {"items": [...], "total": 10}, "ErrorCode": 0, "ErrorMessage": null }
    // 前端收到: { items: [...], total: 10 }

    // 模擬數據
    return Promise.resolve([
      {
        id: '1',
        name: 'Line 官方帳號',
        lineId: '@example',
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ])
  },

  async getById(id: string): Promise<Line> {
    // return await apiClient.get<Line>(`/lines/${id}`)

    const lines = await this.getAll()
    const line = lines.find(l => l.id === id)
    if (!line) {
      throw new Error('Line not found')
    }
    return line
  },

  async create(data: CreateLineDto): Promise<Line> {
    // return await apiClient.post<Line>('/lines', data)

    return Promise.resolve({
      id: Date.now().toString(),
      ...data,
      status: 'active',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    })
  },

  async update(data: UpdateLineDto): Promise<Line> {
    // const { id, ...updateData } = data
    // return await apiClient.put<Line>(`/lines/${id}`, updateData)

    const { id, ...updateData } = data
    const line = await this.getById(id)
    return Promise.resolve({
      ...line,
      ...updateData,
      updatedAt: new Date().toISOString(),
    })
  },

  async delete(id: string): Promise<void> {
    // await apiClient.delete<{ deleted: boolean }>(`/lines/${id}`)
    console.log('delete', id)
    return Promise.resolve()
  },
}
