import { Check, ChevronDown } from 'lucide-react'

import SlotOption from './SlotOption'
import EmptyState from '../../components/ui/EmptyState'
import { formatDateWithoutYear, formatTime } from '../../lib/format'

export default function PlannerCourse({
  entry,
  open,
  focal,
  selectedSlotId,
  clashFor,
  alternativesFor,
  issueMessage,
  onToggle,
  onSelect,
  onUseAlternative,
}) {
  const { course, slots, fixed } = entry
  const selected = slots.find((slot) => slot.id === selectedSlotId) ?? null
  const panelId = `course-${course.id}-slots`

  return (
    <section
      className={`rounded-xl border bg-surface ${
        focal ? 'border-line border-s-[3px] border-s-primary bg-primary-soft' : 'border-line'
      }`}
    >
      <h3>
        <button
          type="button"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => onToggle(course.id)}
          className="flex min-h-14 w-full flex-wrap items-center justify-between gap-x-4 gap-y-1 p-4 text-left"
        >
          <span className="min-w-0">
            <span className="tabular text-base font-semibold text-ink">{course.code}</span>
            <span className="ps-2 text-base text-ink">{course.title}</span>
            <span className="tabular block text-sm text-muted">{`${course.credit_hours} credit hours`}</span>
          </span>
          <span className="flex items-center gap-2">
            {selected ? (
              <span className="tabular flex items-center gap-1.5 text-sm font-medium text-primary">
                <Check size={18} strokeWidth={1.75} aria-hidden="true" />
                {`Planned: ${formatDateWithoutYear(selected.starts_at)}, ${formatTime(selected.starts_at)}`}
              </span>
            ) : (
              <span className="text-sm font-medium text-ink">Choose a time</span>
            )}
            <ChevronDown
              size={20}
              strokeWidth={1.75}
              aria-hidden="true"
              className={`shrink-0 text-muted transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
            />
          </span>
        </button>
      </h3>

      <div id={panelId} hidden={!open} className="px-4 pb-4">
        {issueMessage ? (
          <p role="alert" className="mb-3 rounded-lg bg-clash-soft px-3 py-2 text-sm text-clash">
            {issueMessage}
          </p>
        ) : null}
        {slots.length === 0 ? (
          <EmptyState
            title="No times are available for this course yet."
            body="Your exam office will add exam times. Check back later."
          />
        ) : (
          <fieldset>
            <legend className="sr-only">{`Exam time for ${course.code} ${course.title}`}</legend>
            <div className="space-y-2">
              {slots.map((slot) => (
                <SlotOption
                  key={slot.id}
                  slot={slot}
                  name={`course-${course.id}`}
                  selected={slot.id === selectedSlotId}
                  fixed={fixed}
                  clashMessage={clashFor(slot)}
                  alternatives={alternativesFor(slot)}
                  onSelect={(slotId) => onSelect(course.id, slotId)}
                  onUseAlternative={(alternative) => onUseAlternative(course.id, slot.id, alternative)}
                />
              ))}
            </div>
          </fieldset>
        )}
      </div>
    </section>
  )
}
