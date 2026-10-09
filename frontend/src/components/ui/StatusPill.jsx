import {
  CalendarCheck,
  CalendarClock,
  Check,
  CircleCheck,
  CircleDot,
  CircleSlash,
  Clock,
  History,
  Lock,
  Mail,
  Pencil,
  TriangleAlert,
  Users,
  X,
} from 'lucide-react'

const TONES = {
  neutral: 'bg-sunken text-ink',
  primary: 'bg-primary-soft text-primary',
  warning: 'bg-warning-soft text-warning',
  success: 'bg-success-soft text-success',
  danger: 'bg-danger-soft text-danger',
}

const STATUSES = {
  pending: { label: 'Pending', tone: 'warning', icon: Clock },
  approved: { label: 'Approved', tone: 'success', icon: CircleCheck },
  rejected: { label: 'Rejected', tone: 'danger', icon: X },
  saved: { label: 'Saved', tone: 'success', icon: CalendarCheck },
  planning: { label: 'Planning', tone: 'primary', icon: Pencil },
  branch_pending: { label: 'Branch pending', tone: 'warning', icon: CircleDot },
  invited: { label: 'Invited', tone: 'warning', icon: Mail },
  active: { label: 'Active', tone: 'success', icon: Check },
  inactive: { label: 'Inactive', tone: 'neutral', icon: CircleSlash },
  incomplete: { label: 'Incomplete', tone: 'warning', icon: TriangleAlert },
  complete: { label: 'Complete', tone: 'success', icon: CircleCheck },
  locked: { label: 'Locked', tone: 'neutral', icon: Lock },
  upcoming: { label: 'Upcoming', tone: 'primary', icon: CalendarClock },
  past: { label: 'Past', tone: 'neutral', icon: History },
  in_use: { label: 'In use', tone: 'warning', icon: Users },
}

export default function StatusPill({ status }) {
  const entry = STATUSES[status]
  if (!entry) return null
  const Icon = entry.icon

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${TONES[entry.tone]}`}
    >
      <Icon size={18} strokeWidth={1.75} aria-hidden="true" />
      {entry.label}
    </span>
  )
}
