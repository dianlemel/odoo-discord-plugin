export interface Line {
  id: string
  name: string
  lineId: string
  status: 'active' | 'inactive'
  createdAt: string
  updatedAt: string
}

export interface CreateLineDto {
  name: string
  lineId: string
}

export interface UpdateLineDto extends Partial<CreateLineDto> {
  id: string
  status?: 'active' | 'inactive'
}
