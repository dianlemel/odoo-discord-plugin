import { lineRoutes } from '@/features/line'
import { dealerRoutes } from '@/features/dealer'
import NotFound from './NotFound'

export const routes = [
  ...lineRoutes,
  ...dealerRoutes,
  {
    path: '*',
    element: <NotFound />,
  },
]
