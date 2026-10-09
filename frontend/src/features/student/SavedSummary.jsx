import { Link } from 'react-router'

import { formatDate, formatTime, formatTimeRange } from '../../lib/format'

export default function SavedSummary({ entries }) {
  const rows = [...entries].sort((a, b) => Date.parse(a.starts_at) - Date.parse(b.starts_at))

  return (
    <div className="space-y-6">
      <ul className="divide-y divide-line rounded-xl border border-line bg-surface">
        {rows.map((entry) => (
          <li key={entry.courseId} className="flex flex-wrap items-center justify-between gap-x-6 gap-y-1 px-4 py-3">
            <span className="tabular text-base font-medium text-ink">{entry.courseCode}</span>
            <span className="tabular text-base text-ink">
              {`${formatDate(entry.starts_at)} · ${
                entry.end_time_set ? formatTimeRange(entry.starts_at, entry.ends_at) : formatTime(entry.starts_at)
              }`}
            </span>
          </li>
        ))}
      </ul>

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
        <Link to="/student/date-sheet" className="inline-flex min-h-11 items-center font-medium text-primary">
          View and print date sheet
        </Link>
        <Link to="/student/help" className="inline-flex min-h-11 items-center text-primary">
          Need a change? Send a request.
        </Link>
      </div>
    </div>
  )
}
