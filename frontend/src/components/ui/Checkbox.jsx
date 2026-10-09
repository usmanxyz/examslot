export default function Checkbox({ id, label, describedBy, className = '', ...rest }) {
  return (
    <div className={`flex items-start gap-3 ${className}`}>
      <input
        id={id}
        type="checkbox"
        aria-describedby={describedBy}
        className="mt-0.5 size-5 shrink-0 rounded border-control text-primary accent-[var(--primary)]"
        {...rest}
      />
      <label htmlFor={id} className="text-base text-ink">
        {label}
      </label>
    </div>
  )
}
