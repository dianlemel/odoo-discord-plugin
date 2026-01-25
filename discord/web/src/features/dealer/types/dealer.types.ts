export interface Dealer {
  id: string
  name: string
  code: string
  contact: string
  email: string
  phone: string
  status: 'active' | 'inactive'
  createdAt: string
  updatedAt: string
}

export interface CreateDealerDto {
  name: string
  code: string
  contact: string
  email: string
  phone: string
}

export interface UpdateDealerDto extends Partial<CreateDealerDto> {
  id: string
  status?: 'active' | 'inactive'
}
