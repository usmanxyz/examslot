export default function BarList({ items }) {
  const max = Math.max(1, ...items.map((item) => item.value))

  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.label} className="space-y-1">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="text-[15px] leading-6 text-ink">{item.label}</p>
            <p className="tabular text-sm text-muted">{item.valueLabel}</p>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-sunken">
            <span
              aria-hidden="true"
              style={{ '--bar': `${Math.round((item.value / max) * 100)}%` }}
              className="block h-full w-[var(--bar)] rounded-full bg-primary"
            />
          </div>
        </li>
      ))}
    </ul>
  )
}
