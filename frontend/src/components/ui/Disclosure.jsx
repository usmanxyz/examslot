import { useId, useState } from 'react'
import { ChevronDown } from 'lucide-react'

export default function Disclosure({ summary, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen)
  const panelId = useId()

  return (
    <div className="border-y border-line">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
        className="flex min-h-12 w-full items-center justify-between gap-3 py-3 text-left text-sm font-medium text-ink transition-colors duration-120 hover:bg-sunken"
      >
        <span>{summary}</span>
        <ChevronDown
          size={20}
          strokeWidth={1.75}
          aria-hidden="true"
          className={`shrink-0 text-muted transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>
      <div id={panelId} hidden={!open} className="pb-4">
        {children}
      </div>
    </div>
  )
}
