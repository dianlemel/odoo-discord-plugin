import type { Dealer, CreateDealerDto, UpdateDealerDto } from '../types'
// import { apiClient, ApiError } from '@/core/api'

export const dealerService = {
  async getAll(): Promise<Dealer[]> {
    // 實際使用 API 時的寫法：
    // const result = await apiClient.get<{ items: Dealer[]; total: number }>('/dealers')
    // return result.items
    //
    // 說明：apiClient 會自動提取後端回傳的 Data 欄位
    // 後端格式: { "Data": {"items": [...], "total": 10}, "ErrorCode": 0, "ErrorMessage": null }
    // 前端收到: { items: [...], total: 10 }

    // 模擬數據
    return Promise.resolve([
      {
        id: '1',
        name: '經銷商 A',
        code: 'DEALER_A',
        contact: '張三',
        email: 'dealer-a@example.com',
        phone: '0912-345-678',
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      {
        id: '2',
        name: '經銷商 B',
        code: 'DEALER_B',
        contact: '李四',
        email: 'dealer-b@example.com',
        phone: '0923-456-789',
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ])
  },

  async getById(id: string): Promise<Dealer> {
    // return await apiClient.get<Dealer>(`/dealers/${id}`)

    const dealers = await this.getAll()
    const dealer = dealers.find(d => d.id === id)
    if (!dealer) {
      throw new Error('Dealer not found')
    }
    return dealer
  },

  async create(data: CreateDealerDto): Promise<Dealer> {
    // return await apiClient.post<Dealer>('/dealers', data)

    return Promise.resolve({
      id: Date.now().toString(),
      ...data,
      status: 'active',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    })
  },

  async update(data: UpdateDealerDto): Promise<Dealer> {
    // const { id, ...updateData } = data
    // return await apiClient.put<Dealer>(`/dealers/${id}`, updateData)

    const { id, ...updateData } = data
    const dealer = await this.getById(id)
    return Promise.resolve({
      ...dealer,
      ...updateData,
      updatedAt: new Date().toISOString(),
    })
  },

  async delete(id: string): Promise<void> {
    // await apiClient.delete<{ deleted: boolean }>(`/dealers/${id}`)
    console.log('delete', id)
    return Promise.resolve()
  },
}
