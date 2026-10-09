import { useMemo } from 'react'
import { RouterProvider, createBrowserRouter } from 'react-router'

import { routes } from './router'

export default function App() {
  const router = useMemo(() => createBrowserRouter(routes), [])

  return <RouterProvider router={router} />
}
