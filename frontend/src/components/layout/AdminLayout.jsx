import { Link, NavLink, Outlet } from 'react-router'

import SkipLink from '../ui/SkipLink'
import Button from '../ui/Button'
import Wordmark from '../ui/Wordmark'
import { useAdminAuth } from '../../context/AdminAuthContext'

const LINKS = [
  { to: '/admin', label: 'Dashboard', end: true },
  { to: '/admin/students', label: 'Students', end: false },
  { to: '/admin/requests', label: 'Requests', end: false },
]

function linkClass({ isActive }) {
  return `flex min-h-11 items-center rounded-lg px-3 text-base font-medium transition-colors duration-120 ${
    isActive ? 'bg-primary-soft text-primary' : 'text-ink hover:bg-sunken'
  }`
}

export default function AdminLayout() {
  const { admin, signOut } = useAdminAuth()

  return (
    <div className="flex min-h-dvh flex-col">
      <SkipLink />
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-[90rem] flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
          <Link to="/admin" aria-label="ExamSlot admin">
            <Wordmark />
          </Link>
          <nav aria-label="Main" className="flex flex-wrap items-center gap-1">
            {LINKS.map((link) => (
              <NavLink key={link.to} to={link.to} end={link.end} className={linkClass}>
                {link.label}
              </NavLink>
            ))}
            <Button variant="tertiary" size="sm" onClick={signOut}>
              Sign out
            </Button>
          </nav>
        </div>
      </header>
      <main id="content" className="mx-auto w-full max-w-[90rem] flex-1 px-4 py-8 sm:px-6 lg:px-8">
        {admin ? <p className="pb-6 text-sm text-muted">{`Signed in as ${admin.full_name}`}</p> : null}
        <Outlet />
      </main>
    </div>
  )
}
