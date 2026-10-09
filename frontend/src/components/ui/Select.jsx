import { ChevronDown } from 'lucide-react'

export default function Select({ describedBy, invalid = false, options, className = '', ...rest }) {
  return (
    <div className="relative">
      <select
        aria-describedby={describedBy}
        aria-invalid={invalid || undefined}
        className={`block min-h-11 w-full appearance-none rounded-lg border bg-surface px-3 pe-10 text-base text-ink ${
          invalid ? 'border-danger' : 'border-control'
        } ${className}`}
        {...rest}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown
        size={18}
        strokeWidth={1.75}
        aria-hidden="true"
        className="pointer-events-none absolute inset-y-0 end-3 my-auto text-muted"
      />
    </div>
  )
}
