import { Check, Info } from 'lucide-react'

export default function RadioCard({
  id,
  name,
  value,
  checked = false,
  onChange,
  title,
  description,
  meta,
  unavailableReason,
}) {
  const unavailable = Boolean(unavailableReason)
  const reasonId = unavailable ? `${id}-reason` : undefined

  return (
    <div
      className={`rounded-xl border p-4 transition-colors duration-120 ${
        checked ? 'border-2 border-primary bg-primary-soft' : 'border-line bg-surface'
      } ${unavailable ? 'opacity-80' : ''}`}
    >
      <div className="flex items-start gap-3">
        <input
          id={id}
          type="radio"
          name={name}
          value={value}
          checked={checked}
          aria-disabled={unavailable || undefined}
          aria-describedby={reasonId}
          onChange={unavailable ? undefined : onChange}
          className="mt-1 size-5 shrink-0 accent-[var(--primary)]"
        />
        <div className="min-w-0 flex-1 space-y-1">
          <label htmlFor={id} className="block text-[17px] leading-6 font-semibold text-ink">
            {title}
          </label>
          {description ? <p className="text-sm text-muted">{description}</p> : null}
          {meta ? <p className="tabular text-sm text-muted">{meta}</p> : null}
          {unavailable ? (
            <p id={reasonId} className="flex items-start gap-2 text-sm text-warning">
              <Info size={18} strokeWidth={1.75} aria-hidden="true" className="mt-0.5 shrink-0" />
              <span>{unavailableReason}</span>
            </p>
          ) : null}
        </div>
        {checked ? (
          <span className="flex items-center gap-1 text-sm font-medium text-primary">
            <Check size={18} strokeWidth={1.75} aria-hidden="true" />
            Selected
          </span>
        ) : null}
      </div>
    </div>
  )
}
