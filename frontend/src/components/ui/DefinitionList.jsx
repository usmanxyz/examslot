const COLUMNS = {
  1: 'sm:grid-cols-1',
  2: 'sm:grid-cols-2',
  3: 'sm:grid-cols-3',
}

export default function DefinitionList({ items, columns = 1 }) {
  return (
    <dl className={`grid grid-cols-1 gap-x-8 gap-y-4 ${COLUMNS[columns]}`}>
      {items.map((item) => (
        <div key={item.term} className="space-y-1">
          <dt className="text-sm font-medium text-muted">{item.term}</dt>
          <dd className="tabular text-[15px] leading-6 text-ink">{item.value}</dd>
        </div>
      ))}
    </dl>
  )
}
