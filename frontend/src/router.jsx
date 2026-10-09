import { Navigate } from 'react-router'

import PublicLayout from './components/layout/PublicLayout'
import RootProviders from './components/layout/RootProviders'
import StudentLayout from './components/layout/StudentLayout'
import RedirectIfSignedIn from './guards/RedirectIfSignedIn'
import RequireStudent from './guards/RequireStudent'
import StudentFlowGate from './guards/StudentFlowGate'

function page(loader) {
  return async () => ({ Component: (await loader()).default })
}

export const routes = [
  {
    path: '/',
    Component: RootProviders,
    children: [
      {
        Component: PublicLayout,
        children: [
          { index: true, element: <Navigate to="/login" replace /> },
          {
            Component: RedirectIfSignedIn,
            children: [{ path: 'login', lazy: page(() => import('./pages/public/LoginPage')) }],
          },
          { path: 'set-password', lazy: page(() => import('./pages/public/SetPasswordPage')) },
          { path: '*', lazy: page(() => import('./pages/public/NotFoundPage')) },
        ],
      },
      {
        Component: RequireStudent,
                children: [
          {
            Component: StudentLayout,
            children: [
              {
                Component: StudentFlowGate,
                children: [
                  { path: 'student', lazy: page(() => import('./pages/student/DashboardPage')) },
                  { path: 'student/branch', lazy: page(() => import('./pages/student/BranchPage')) },
                ],
              },
            ],
          },
        ],
      },
    ],
  },
]
