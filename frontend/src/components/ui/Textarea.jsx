export default function Textarea({ describedBy, invalid = false, counter, className = '', ...rest }) {
  return (
    <div className="space-y-1">
      <textarea
        aria-describedby={describedBy}
        aria-invalid={invalid || undefined}
        className={`block w-full rounded-lg border bg-surface px-3 py-2 text-base text-ink ${
          invalid ? 'border-danger' : 'border-control'
        } ${className}`}
        {...rest}
      />
      {counter ? <p className="tabular text-right text-[13px] leading-[18px] text-muted">{counter}</p> : null}
    </div>
  )
}
