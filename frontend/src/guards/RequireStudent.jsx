import { Navigate, Outlet, useLocation } from 'react-router'

import Skeleton from '../components/ui/Skeleton'
import { useStudentAuth } from '../context/StudentAuthContext'

export default function RequireStudent() {
  const { status } = useStudentAuth()
  const location = useLocation()

  if (status === 'loading') {
    return (
      <div aria-busy="true" className="mx-auto max-w-[72rem] space-y-4 px-4 py-10">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-5 w-80" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  if (status !== 'signedIn') {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname, notice: 'Sign in to continue.' }}
      />
    )
  }

  return <Outlet />
}
