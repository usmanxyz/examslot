import { useId, useRef } from 'react'

export default function Tabs({ tabs, value, onChange }) {
  const baseId = useId()
  const list = useRef(null)

  const onKeyDown = (event) => {
    const index = tabs.findIndex((tab) => tab.value === value)
    const moves = { ArrowRight: 1, ArrowLeft: -1 }
    if (event.key === 'Home') {
      event.preventDefault()
      onChange(tabs[0].value)
      return
    }
    if (event.key === 'End') {
      event.preventDefault()
      onChange(tabs[tabs.length - 1].value)
      return
    }
    const move = moves[event.key]
    if (!move) return
    event.preventDefault()
    const next = (index + move + tabs.length) % tabs.length
    onChange(tabs[next].value)
    list.current?.querySelector(`#${CSS.escape(`${baseId}-${tabs[next].value}`)}`)?.focus()
  }

  return (
    <div
      ref={list}
      role="tablist"
      aria-label="Student sections"
      onKeyDown={onKeyDown}
      className="flex flex-wrap gap-1 border-b border-line"
    >
      {tabs.map((tab) => {
        const selected = tab.value === value
        return (
          <button
            key={tab.value}
            id={`${baseId}-${tab.value}`}
            type="button"
            role="tab"
            aria-selected={selected}
            aria-controls={`${baseId}-${tab.value}-panel`}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(tab.value)}
            className={`-mb-px min-h-11 border-b-2 px-4 text-base font-medium transition-colors duration-120 ${
              selected ? 'border-primary text-primary' : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}

export function TabPanel({ children }) {
  return (
    <div role="tabpanel" tabIndex={0} className="pt-6">
      {children}
    </div>
  )
}
