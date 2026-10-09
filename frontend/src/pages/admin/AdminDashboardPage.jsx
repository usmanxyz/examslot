import { useCallback } from 'react'
import { Link } from 'react-router'

import BarList from '../../components/ui/BarList'
import EmptyState from '../../components/ui/EmptyState'
import ErrorState from '../../components/ui/ErrorState'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useQuery } from '../../hooks/useQuery'
import { getDashboard } from '../../services/admin/dashboardService'
import { formatDateShort, formatClockTime } from '../../lib/format'

function Tile({ to, label, value, tone = 'neutral' }) {
  const toneClass =
    tone === 'warning'
      ? 'border-warning bg-warning-soft text-warning'
      : 'border-line bg-surface text-ink'

  return (
    <Link
      to={to}
      className={`block rounded-xl border p-5 transition-colors duration-120 hover:border-primary ${toneClass}`}
    >
      <p className="tabular font-serif text-[34px] leading-[42px] font-semibold">{value}</p>
      <p className="mt-1 text-[15px] text-muted">{label}</p>
    </Link>
  )
}

function Panel({ title, children }) {
  return (
    <section className="rounded-xl border border-line bg-surface p-6">
      <h2 className="font-serif text-[22px] leading-7 font-semibold tracking-[-0.01em]">{title}</h2>
      <div className="mt-5">{children}</div>
    </section>
  )
}

export default function AdminDashboardPage() {
  useDocumentTitle('Dashboard')
  const { api } = useAdminAuth()
  const load = useCallback((signal) => getDashboard(api, signal), [api])
  const { status, data, error, reload } = useQuery(load)

  if (status === 'loading') {
    return (
      <div aria-busy="true" className="space-y-8">
        <Skeleton className="h-10 w-56" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {[0, 1, 2, 3, 4].map((tile) => (
            <Skeleton key={tile} className="h-28 w-full rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-60 w-full rounded-xl" />
      </div>
    )
  }

  if (status === 'error') return <ErrorState message={error?.message} onRetry={reload} />

  const pending = data.requests.pending_branch_change + data.requests.pending_date_sheet_change
  const byBranch = data.saved_by_branch.map((entry) => ({
    label: `${entry.branch.code} ${entry.branch.name}`,
    value: entry.count,
    valueLabel: entry.count === 1 ? '1 date sheet' : `${entry.count} date sheets`,
  }))
  const fullest = data.fullest_slots.map((slot) => ({
    label: `${slot.course_code} ${formatDateShort(slot.date)} ${formatClockTime(slot.start_time)} ${slot.branch_code}`,
    value: slot.taken,
    valueLabel: `${slot.taken} of ${slot.capacity} seats taken`,
  }))

  return (
    <div className="space-y-8">
      <PageHeader title="Dashboard" meta="Everything the exam office needs at a glance." />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Tile to="/admin/students" label="Students" value={data.students.total} />
        <Tile to="/admin/students?account_status=invited" label="Invited" value={data.students.invited} />
        <Tile
          to="/admin/assignments?status=incomplete"
          label="Assignment incomplete"
          value={data.students.assignment_incomplete}
        />
        <Tile to="/admin/students?progress=saved" label="Saved date sheets" value={data.students.saved} />
        <Tile
          to="/admin/requests?status=pending"
          label="Pending requests"
          value={pending}
          tone={pending > 0 ? 'warning' : 'neutral'}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Saved date sheets by branch">
          {byBranch.length > 0 ? (
            <BarList items={byBranch} />
          ) : (
            <EmptyState title="No saved date sheets yet" body="Counts appear once students save their exams." />
          )}
        </Panel>
        <Panel title="Fullest upcoming slots">
          {fullest.length > 0 ? (
            <BarList items={fullest} />
          ) : (
            <EmptyState title="No upcoming slots" body="Add exam slots so students can plan." />
          )}
        </Panel>
      </div>

      <p className="text-sm text-muted">
        {data.slots.upcoming} upcoming exam slots. {data.requests.open_approvals} approved requests waiting to be
        used.
      </p>
    </div>
  )
}
