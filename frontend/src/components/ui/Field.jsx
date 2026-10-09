import { CircleAlert } from 'lucide-react'

export default function Field({ id, label, hint, error, optional = false, children }) {
  const hintId = hint ? `${id}-hint` : undefined
  const errorId = error ? `${id}-error` : undefined

  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {label}
        {optional ? <span className="font-normal text-muted"> (optional)</span> : null}
      </label>
      {hint ? (
        <p id={hintId} className="text-sm text-muted">
          {hint}
        </p>
      ) : null}
      {children({
        id,
        describedBy: [hintId, errorId].filter(Boolean).join(' ') || undefined,
        invalid: Boolean(error),
      })}
      {error ? (
        <p id={errorId} className="flex items-start gap-2 text-sm text-danger">
          <CircleAlert size={18} strokeWidth={1.75} aria-hidden="true" className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </p>
      ) : null}
    </div>
  )
}
