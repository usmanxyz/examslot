import { useEffect, useState } from 'react'
import { Search, X } from 'lucide-react'

import { useDebouncedValue } from '../../hooks/useDebouncedValue'

export default function SearchInput({ id = 'search', label = 'Search', value, onChange, placeholder }) {
  const [text, setText] = useState(value)
  const [lastValue, setLastValue] = useState(value)
  const debounced = useDebouncedValue(text, 300)

  if (value !== lastValue) {
    setLastValue(value)
    setText(value)
  }

  useEffect(() => {
    if (debounced === lastValue) return
    onChange(debounced)
  }, [debounced, lastValue, onChange])

  return (
    <div className="relative w-full sm:max-w-[22rem]">
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <Search
        size={18}
        strokeWidth={1.75}
        aria-hidden="true"
        className="pointer-events-none absolute inset-y-0 start-3 my-auto text-muted"
      />
      <input
        id={id}
        type="search"
        value={text}
        placeholder={placeholder}
        onChange={(event) => setText(event.target.value)}
        className="block min-h-11 w-full rounded-lg border border-control bg-surface ps-10 pe-10 text-base text-ink"
      />
      {text ? (
        <button
          type="button"
          aria-label="Clear search"
          onClick={() => setText('')}
          className="absolute inset-y-0 end-0 inline-flex w-10 items-center justify-center text-muted hover:text-ink"
        >
          <X size={18} strokeWidth={1.75} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  )
}
