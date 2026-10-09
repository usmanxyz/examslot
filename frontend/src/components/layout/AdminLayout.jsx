import { useCallback, useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router'
import {
  BookOpen,
  Building2,
  CalendarClock,
  LayoutDashboard,
  ListChecks,
  Menu,
  MessageSquareWarning,
  Users,
} from 'lucide-react'

import SiteFooter from './SiteFooter'
import Button from '../ui/Button'
import Drawer from '../ui/Drawer'
import IconButton from '../ui/IconButton'
import SkipLink from '../ui/SkipLink'
import Wordmark from '../ui/Wordmark'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useQuery } from '../../hooks/useQuery'
import { getDashboard } from '../../services/admin/dashboardService'

const LINKS = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/students', label: 'Students', icon: Users, end: false },
  { to: '/admin/assignments', label: 'Assignments', icon: ListChecks, end: false },
  { to: '/admin/slots', label: 'Exam slots', icon: CalendarClock, end: false },
  { to: '/admin/requests', label: 'Requests', icon: MessageSquareWarning, end: false },
  { to: '/admin/branches', label: 'Branches', icon: Building2, end: false },
  { to: '/admin/courses', label: 'Courses', icon: BookOpen, end: false },
]

function linkClass({ isActive }) {
  return `flex min-h-11 items-center gap-3 rounded-lg px-3 text-base font-medium transition-colors duration-120 ${
    isActive ? 'bg-primary-soft text-primary' : 'text-ink hover:bg-sunken'
  }`
}

function Navigation({ pendingCount, onNavigate }) {
  return (
    <nav aria-label="Admin" className="flex flex-col gap-1">
      {LINKS.map((link) => {
        const Icon = link.icon
        return (
          <NavLink key={link.to} to={link.to} end={link.end} className={linkClass} onClick={onNavigate}>
            <Icon size={20} strokeWidth={1.75} aria-hidden="true" />
            <span className="flex-1">{link.label}</span>
            {link.to === '/admin/requests' && pendingCount > 0 ? (
              <span className="tabular rounded-full bg-warning-soft px-2 py-0.5 text-sm font-medium text-warning">
                {pendingCount}
              </span>
            ) : null}
          </NavLink>
        )
      })}
    </nav>
  )
}

export default function AdminLayout() {
  const { api, me, signOut } = useAdminAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const load = useCallback((signal) => getDashboard(api, signal), [api])
  const { data } = useQuery(load)
  const pendingCount =
    (data?.requests?.pending_branch_change ?? 0) + (data?.requests?.pending_date_sheet_change ?? 0)

  return (
    <div className="flex min-h-dvh flex-col">
      <SkipLink />
      <div className="flex flex-1">
        <aside className="print-hidden hidden w-[16rem] shrink-0 flex-col border-e border-line px-4 py-6 lg:flex">
          <Link to="/admin" aria-label="ExamSlot admin" className="px-3">
            <Wordmark />
          </Link>
          <div className="mt-8 flex-1">
            <Navigation pendingCount={pendingCount} />
          </div>
          <div className="space-y-1 border-t border-line pt-4">
            <NavLink to="/admin/account" className={linkClass}>
              Account
            </NavLink>
            <Button variant="tertiary" className="w-full justify-start" onClick={signOut}>
              Sign out
            </Button>
            {me ? <p className="px-3 pt-2 text-[13px] leading-[18px] text-muted">{me.email}</p> : null}
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="print-hidden border-b border-line lg:hidden">
            <div className="flex items-center justify-between gap-4 px-4 py-3">
              <Link to="/admin" aria-label="ExamSlot admin">
                <Wordmark />
              </Link>
              <IconButton label="Open menu" icon={Menu} onClick={() => setMenuOpen(true)} />
            </div>
          </header>

          <Drawer open={menuOpen} onClose={() => setMenuOpen(false)} title="Menu">
            <Navigation pendingCount={pendingCount} onNavigate={() => setMenuOpen(false)} />
            <div className="mt-6 space-y-1 border-t border-line pt-4">
              <NavLink to="/admin/account" className={linkClass} onClick={() => setMenuOpen(false)}>
                Account
              </NavLink>
              <Button variant="secondary" className="w-full" onClick={signOut}>
                Sign out
              </Button>
            </div>
          </Drawer>

          <main id="content" className="mx-auto w-full max-w-[90rem] flex-1 px-4 py-8 sm:px-6 lg:px-8">
            <Outlet />
          </main>
          <SiteFooter />
        </div>
      </div>
    </div>
  )
}
