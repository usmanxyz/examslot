import Button from '../../components/ui/Button'
import { formatDateWithoutYear, formatTime, formatYear } from '../../lib/format'

export default function AgendaRail({ picks, progress, complete, onReview }) {
  const days = picks.reduce((groups, pick) => {
    const key = formatDateWithoutYear(pick.slot.starts_at)
    const group = groups.find((item) => item.key === key)
    if (group) group.picks.push(pick)
    else groups.push({ key, picks: [pick] })
    return groups
  }, [])
  const year = picks.length > 0 ? formatYear(picks[0].slot.starts_at) : null

  return (
    <aside aria-labelledby="agenda-heading" className="space-y-4 rounded-xl border border-line bg-surface p-4">
      <div>
        <h3 id="agenda-heading" className="text-[17px] leading-6 font-semibold text-ink">
          Your agenda
        </h3>
        {year ? <p className="tabular text-sm text-muted">{year}</p> : null}
      </div>

      {days.length === 0 ? (
        <p className="text-sm text-muted">Your picks appear here as you choose them.</p>
      ) : (
        <dl className="space-y-3">
          {days.map((day) => (
            <div key={day.key} className="space-y-1">
              <dt className="tabular text-sm font-medium text-ink">{day.key}</dt>
              {day.picks.map((pick) => (
                <dd key={pick.courseId} className="tabular text-sm text-muted">
                  {`${formatTime(pick.slot.starts_at)} · ${pick.courseCode}`}
                </dd>
              ))}
            </div>
          ))}
        </dl>
      )}

      <p aria-live="polite" className="tabular border-t border-line pt-4 text-sm font-medium text-ink">
        {progress}
      </p>

      {complete ? null : (
        <p id="agenda-hint" className="text-sm text-muted">
          Choose a time for every course to continue.
        </p>
      )}

      <Button
        className="w-full"
        disabled={!complete}
        aria-describedby={complete ? undefined : 'agenda-hint'}
        onClick={onReview}
      >
        Review date sheet
      </Button>
    </aside>
  )
}
