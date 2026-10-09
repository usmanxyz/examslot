import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router'
import { Menu } from 'lucide-react'

import SiteFooter from './SiteFooter'
import Button from '../ui/Button'
import Drawer from '../ui/Drawer'
import IconButton from '../ui/IconButton'
import SkipLink from '../ui/SkipLink'
import ThemeSwitcher from '../ui/ThemeSwitcher'
import Wordmark from '../ui/Wordmark'
import { useStudentAuth } from '../../context/StudentAuthContext'

function linkClass({ isActive }) {
  return `flex min-h-11 items-center rounded-lg px-3 text-base font-medium transition-colors duration-120 ${
    isActive ? 'bg-primary-soft text-primary' : 'text-ink hover:bg-sunken'
  }`
}

export default function StudentLayout() {
  const { me, signOut } = useStudentAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const savedDateSheet = Boolean(me?.date_sheet_saved_at)

  const links = [
    { to: '/student', label: 'Dashboard', end: true },
    ...(savedDateSheet ? [{ to: '/student/date-sheet', label: 'Date sheet', end: false }] : []),
    { to: '/student/help', label: 'Need help', end: false },
    { to: '/student/account', label: 'Account', end: false },
  ]

  return (
    <div className="flex min-h-dvh flex-col">
      <SkipLink />
      <header className="print-hidden border-b border-line">
        <div className="mx-auto flex max-w-[72rem] items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
          <Link to="/student" aria-label="ExamSlot dashboard">
            <Wordmark />
          </Link>
          <nav aria-label="Main" className="hidden items-center gap-1 sm:flex">
            {links.map((link) => (
              <NavLink key={link.to} to={link.to} end={link.end} className={linkClass}>
                {link.label}
              </NavLink>
            ))}
            <Button variant="tertiary" size="sm" onClick={signOut}>
              Sign out
            </Button>
          </nav>
          <IconButton label="Open menu" icon={Menu} className="sm:hidden" onClick={() => setMenuOpen(true)} />
        </div>
      </header>

      <Drawer open={menuOpen} onClose={() => setMenuOpen(false)} title="Menu">
        <nav aria-label="Main" className="flex flex-col gap-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={linkClass}
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-6 space-y-4">
          <ThemeSwitcher />
          <Button variant="secondary" className="w-full" onClick={signOut}>
            Sign out
          </Button>
        </div>
      </Drawer>

      <main id="content" className="mx-auto w-full max-w-[72rem] flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <Outlet />
      </main>
      <SiteFooter />
    </div>
  )
}
