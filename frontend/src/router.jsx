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
            children: [
              { path: 'login', lazy: page(() => import('./pages/public/LoginPage')) },
              { path: 'forgot-password', lazy: page(() => import('./pages/public/ForgotPasswordPage')) },
            ],
          },
          { path: 'set-password', lazy: page(() => import('./pages/public/SetPasswordPage')) },
          { path: 'about', lazy: page(() => import('./pages/public/AboutPage')) },
          { path: 'contact', lazy: page(() => import('./pages/public/ContactPage')) },
          { path: 'terms', lazy: page(() => import('./pages/public/TermsPage')) },
          { path: 'privacy', lazy: page(() => import('./pages/public/PrivacyPage')) },
          { path: 'disclaimer', lazy: page(() => import('./pages/public/DisclaimerPage')) },
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
                  {
                    path: 'student/date-sheet',
                    lazy: page(() => import('./pages/student/DateSheetPage')),
                  },
                ],
              },
              { path: 'student/help', lazy: page(() => import('./pages/student/HelpPage')) },
              { path: 'student/account', lazy: page(() => import('./pages/student/AccountPage')) },
            ],
          },
        ],
      },
    ],
  },
]
