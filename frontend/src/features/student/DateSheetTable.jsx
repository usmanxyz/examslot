import { formatDate, formatDateWithoutYear, formatTime, formatTimeRange } from '../../lib/format'

function time(entry) {
  return entry.end_time_set ? formatTimeRange(entry.starts_at, entry.ends_at) : formatTime(entry.starts_at)
}

export default function DateSheetTable({ entries }) {
  return (
    <>
      <div className="print-show hidden sm:block">
        <table className="print-table w-full border-collapse text-left text-sm">
          <caption className="sr-only">Your exams sorted by date</caption>
          <thead>
            <tr className="bg-sunken">
              <th scope="col" className="px-4 py-3 font-medium text-muted">
                Course code
              </th>
              <th scope="col" className="px-4 py-3 font-medium text-muted">
                Course title
              </th>
              <th scope="col" className="px-4 py-3 font-medium text-muted">
                Date
              </th>
              <th scope="col" className="px-4 py-3 font-medium text-muted">
                Day
              </th>
              <th scope="col" className="px-4 py-3 font-medium text-muted">
                Time
              </th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.course_code} className="border-t border-line">
                <td className="tabular px-4 py-3 font-medium text-ink">{entry.course_code}</td>
                <td className="px-4 py-3 text-ink">{entry.course_title}</td>
                <td className="tabular px-4 py-3 text-ink">{formatDate(entry.starts_at)}</td>
                <td className="px-4 py-3 text-ink">{entry.day}</td>
                <td className="tabular px-4 py-3 text-ink">{time(entry)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ul className="print-hidden space-y-3 sm:hidden">
        {entries.map((entry) => (
          <li key={entry.course_code} className="rounded-xl border border-line bg-surface p-4">
            <h3 className="tabular text-[17px] leading-6 font-semibold text-ink">
              {`${formatDateWithoutYear(entry.starts_at)}`}
            </h3>
            <p className="tabular text-sm text-muted">{time(entry)}</p>
            <p className="tabular mt-2 text-base font-medium text-ink">{entry.course_code}</p>
            <p className="text-base text-ink">{entry.course_title}</p>
          </li>
        ))}
      </ul>
    </>
  )
}
