import { Outlet } from 'react-router'

import ServerWakeNotice from '../ui/ServerWakeNotice'
import Toaster from '../ui/Toaster'
import { ServerStatusProvider } from '../../context/ServerStatusContext'
import { StudentAuthProvider } from '../../context/StudentAuthContext'
import { ThemeProvider } from '../../context/ThemeContext'
import { ToastProvider } from '../../context/ToastContext'

export default function RootProviders() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <ServerStatusProvider>
          <StudentAuthProvider>
            <ServerWakeNotice />
            <Outlet />
            <Toaster />
          </StudentAuthProvider>
        </ServerStatusProvider>
      </ToastProvider>
    </ThemeProvider>
  )
}
