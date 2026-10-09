import { Link, Outlet } from 'react-router'

import SiteFooter from './SiteFooter'
import SkipLink from '../ui/SkipLink'
import ThemeSwitcher from '../ui/ThemeSwitcher'
import Wordmark from '../ui/Wordmark'

export default function PublicLayout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SkipLink />
      <header className="print-hidden">
        <div className="mx-auto flex max-w-[72rem] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <Link to="/login" aria-label="ExamSlot home">
            <Wordmark />
          </Link>
          <div className="w-[16rem] max-w-[50%]">
            <ThemeSwitcher />
          </div>
        </div>
      </header>
      <main id="content" className="flex-1 px-4 sm:px-6 lg:px-8">
        <Outlet />
      </main>
      <SiteFooter />
    </div>
  )
}
