export default function TextInput({ describedBy, invalid = false, className = '', ...rest }) {
  return (
    <input
      aria-describedby={describedBy}
      aria-invalid={invalid || undefined}
      className={`block min-h-11 w-full rounded-lg border bg-surface px-3 text-base text-ink ${
        invalid ? 'border-danger' : 'border-control'
      } ${className}`}
      {...rest}
    />
  )
}
