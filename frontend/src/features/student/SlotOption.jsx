import { Check, Lock } from 'lucide-react'

import Button from '../../components/ui/Button'
import ClashMessage from './ClashMessage'
import { formatDateWithoutYear, formatTime, formatTimeRange } from '../../lib/format'

function slotTime(slot) {
  return slot.end_time_set ? formatTimeRange(slot.starts_at, slot.ends_at) : formatTime(slot.starts_at)
}

export default function SlotOption({
  slot,
  name,
  selected,
  fixed,
  clashMessage,
  alternatives,
  onSelect,
  onUseAlternative,
}) {
  const inputId = `slot-${slot.id}`
  const clashId = `${inputId}-clash`
  const blocked = Boolean(clashMessage) || fixed

  return (
    <div
      className={`rounded-lg border p-3 transition-colors duration-120 ${
        selected ? 'border-2 border-primary bg-primary-soft' : 'border-line bg-surface'
      }`}
    >
      <div className="flex min-h-14 items-start gap-3">
        <input
          id={inputId}
          type="radio"
          name={name}
          value={slot.id}
          checked={selected}
          aria-disabled={blocked || undefined}
          aria-describedby={clashMessage ? clashId : undefined}
          onChange={blocked ? undefined : () => onSelect(slot.id)}
          className="mt-1.5 size-5 shrink-0 accent-[var(--primary)]"
        />
        <div className="min-w-0 flex-1 space-y-1">
          <label htmlFor={inputId} className="tabular block text-base font-medium text-ink">
            {formatDateWithoutYear(slot.starts_at)}
            <span className="ps-2 font-normal">{slotTime(slot)}</span>
          </label>
          {slot.seats_left <= 5 ? (
            <p className="tabular text-sm text-warning">{`${slot.seats_left} seats left`}</p>
          ) : null}
          {fixed ? (
            <p className="flex items-start gap-2 text-sm text-muted">
              <Lock size={18} strokeWidth={1.75} aria-hidden="true" className="mt-0.5 shrink-0" />
              <span>This exam has started, so it cannot change.</span>
            </p>
          ) : null}
          {clashMessage ? <ClashMessage id={clashId} message={clashMessage} /> : null}
          {alternatives.length > 0 ? (
            <div className="flex flex-col items-start gap-1 pt-1">
              <span className="text-sm text-muted">Other times:</span>
              {alternatives.map((alternative) => (
                <Button
                  key={`${alternative.courseCode}-${alternative.slot.id}`}
                  variant="tertiary"
                  size="sm"
                  onClick={() => onUseAlternative(alternative)}
                >
                  {`Move ${alternative.courseCode} to ${formatDateWithoutYear(alternative.slot.starts_at)} at ${formatTime(alternative.slot.starts_at)}`}
                </Button>
              ))}
            </div>
          ) : null}
        </div>
        {selected ? (
          <span className="flex shrink-0 items-center gap-1 text-sm font-medium text-primary">
            <Check size={18} strokeWidth={1.75} aria-hidden="true" />
            Selected
          </span>
        ) : null}
      </div>
    </div>
  )
}
