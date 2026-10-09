import { Navigate } from 'react-router'

import AdminLayout from './components/layout/AdminLayout'
import PublicLayout from './components/layout/PublicLayout'
import RootProviders from './components/layout/RootProviders'
import StudentLayout from './components/layout/StudentLayout'
import RedirectIfAdmin from './guards/RedirectIfAdmin'
import RedirectIfSignedIn from './guards/RedirectIfSignedIn'
import RequireAdmin from './guards/RequireAdmin'
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
          {
            Component: RedirectIfAdmin,
            children: [
              { path: 'admin/login', lazy: page(() => import('./pages/admin/AdminLoginPage')) },
            ],
          },
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
      {
        Component: RequireAdmin,
        children: [
          {
            Component: AdminLayout,
            children: [
              { path: 'admin', lazy: page(() => import('./pages/admin/AdminDashboardPage')) },
              { path: 'admin/students', lazy: page(() => import('./pages/admin/StudentsPage')) },
              { path: 'admin/students/new', lazy: page(() => import('./pages/admin/StudentNewPage')) },
              {
                path: 'admin/students/:studentId',
                lazy: page(() => import('./pages/admin/StudentDetailPage')),
              },
              {
                path: 'admin/students/:studentId/edit',
                lazy: page(() => import('./pages/admin/StudentEditPage')),
              },
              { path: 'admin/assignments', lazy: page(() => import('./pages/admin/AssignmentsPage')) },
              {
                path: 'admin/assignments/:studentId',
                lazy: page(() => import('./pages/admin/AssignmentEditorPage')),
              },
              { path: 'admin/slots', lazy: page(() => import('./pages/admin/SlotsPage')) },
              { path: 'admin/requests', lazy: page(() => import('./pages/admin/RequestsPage')) },
              { path: 'admin/branches', lazy: page(() => import('./pages/admin/BranchesPage')) },
              { path: 'admin/courses', lazy: page(() => import('./pages/admin/CoursesPage')) },
              { path: 'admin/account', lazy: page(() => import('./pages/admin/AdminAccountPage')) },
            ],
          },
        ],
      },
    ],
  },
]
