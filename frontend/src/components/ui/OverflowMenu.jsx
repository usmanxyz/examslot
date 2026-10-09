import { useEffect, useRef, useState } from 'react'
import { MoreHorizontal } from 'lucide-react'

import IconButton from './IconButton'

export default function OverflowMenu({ label = 'More actions', items }) {
  const [open, setOpen] = useState(false)
  const container = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onPointerDown = (event) => {
      if (!container.current?.contains(event.target)) setOpen(false)
    }
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  return (
    <div ref={container} className="relative inline-block text-start">
      <IconButton
        label={label}
        icon={MoreHorizontal}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((current) => !current)}
      />
      {open ? (
        <div
          role="menu"
          className="absolute end-0 z-30 mt-1 w-[15rem] rounded-xl border border-line bg-surface py-1 shadow-overlay"
        >
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              role="menuitem"
              disabled={item.disabled}
              title={item.disabledReason}
              onClick={() => {
                setOpen(false)
                item.onSelect()
              }}
              className={`flex min-h-11 w-full items-center px-4 text-start text-base disabled:cursor-not-allowed disabled:opacity-50 ${
                item.danger ? 'text-danger hover:bg-danger-soft' : 'text-ink hover:bg-sunken'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
