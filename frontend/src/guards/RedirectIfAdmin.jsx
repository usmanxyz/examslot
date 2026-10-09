import { Navigate, Outlet } from 'react-router'

import { useAdminAuth } from '../context/AdminAuthContext'

export default function RedirectIfAdmin() {
  const { status } = useAdminAuth()

  if (status === 'signedIn') return <Navigate to="/admin" replace />

  return <Outlet />
}
