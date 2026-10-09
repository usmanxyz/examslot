import { useCallback, useEffect, useId, useRef } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

import IconButton from './IconButton'

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export default function Dialog({ open, onClose, title, description, footer, placement = 'center', children }) {
  const panel = useRef(null)
  const opener = useRef(null)
  const titleId = useId()
  const descriptionId = useId()

  const focusables = useCallback(() => {
    if (!panel.current) return []
    return Array.from(panel.current.querySelectorAll(FOCUSABLE))
  }, [])

  useEffect(() => {
    if (!open) return undefined
    opener.current = document.activeElement
    const first = focusables()[0] ?? panel.current
    first?.focus()
    const trigger = opener.current
    return () => {
      if (trigger instanceof HTMLElement) trigger.focus()
    }
  }, [open, focusables])

  useEffect(() => {
    if (!open) return undefined
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
        return
      }
      if (event.key !== 'Tab') return
      const items = focusables()
      if (items.length === 0) return
      const first = items[0]
      const last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [open, onClose, focusables])

  if (!open) return null

  const panelClass =
    placement === 'drawer'
      ? 'h-full w-[18rem] max-w-[85vw] rounded-none border-r border-line'
      : 'max-h-[90dvh] w-full max-w-[36rem] rounded-xl border border-line'

  return createPortal(
    <div
      className={`fixed inset-0 z-40 flex bg-[rgb(23_35_58/0.45)] motion-safe:animate-[overlay-in_200ms_ease-out] ${
        placement === 'drawer' ? 'justify-start' : 'items-center justify-center p-4'
      }`}
    >
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
        className={`flex flex-col overflow-hidden bg-surface shadow-overlay motion-safe:animate-[panel-in_200ms_ease-out] ${panelClass}`}
      >
        <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <h2 id={titleId} className="text-xl leading-7 font-semibold text-ink">
            {title}
          </h2>
          <IconButton label="Close" icon={X} onClick={onClose} />
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          {description ? (
            <p id={descriptionId} className="text-base text-ink">
              {description}
            </p>
          ) : null}
          {children}
        </div>
        {footer ? (
          <div className="flex flex-wrap justify-end gap-3 border-t border-line px-5 py-4">{footer}</div>
        ) : null}
      </div>
    </div>,
    document.body,
  )
}
