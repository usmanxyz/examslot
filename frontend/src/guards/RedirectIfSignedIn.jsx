import { Navigate, Outlet } from 'react-router'

import { useStudentAuth } from '../context/StudentAuthContext'

export default function RedirectIfSignedIn() {
  const { status } = useStudentAuth()

  if (status === 'signedIn') return <Navigate to="/student" replace />

  return <Outlet />
}
