import { Navigate, Outlet } from 'react-router'

import Skeleton from '../components/ui/Skeleton'
import { useAdminAuth } from '../context/AdminAuthContext'

export default function RequireAdmin() {
  const { status } = useAdminAuth()

  if (status === 'loading') {
    return (
      <div aria-busy="true" className="mx-auto max-w-[90rem] space-y-4 px-4 py-10">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-5 w-80" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  if (status !== 'signedIn') {
    return <Navigate to="/admin/login" replace state={{ notice: 'Sign in to continue.' }} />
  }

  return <Outlet />
}
