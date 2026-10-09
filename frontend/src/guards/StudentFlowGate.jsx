import { Navigate, Outlet, useLocation } from 'react-router'

import { useStudentAuth } from '../context/StudentAuthContext'

export function nextStudentPath(pathname, me) {
  if (!me) return null
  const branchOpen = me.branch === null || me.can_change_branch === true
  if (pathname === '/student' && branchOpen) return '/student/branch'
  if (pathname === '/student/branch' && !branchOpen) return '/student'
  if (pathname === '/student/date-sheet' && !me.date_sheet_saved_at) return '/student'
  return null
}

export default function StudentFlowGate() {
  const { me } = useStudentAuth()
  const location = useLocation()
  const target = nextStudentPath(location.pathname, me)

  if (target) return <Navigate to={target} replace />

  return <Outlet />
}
