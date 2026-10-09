import { useEffect, useState } from 'react'
import { CircleCheck, X } from 'lucide-react'

import IconButton from './IconButton'
import { useToast } from '../../context/ToastContext'

function Toast({ toast, onDismiss }) {
  const [paused, setPaused] = useState(false)

  useEffect(() => {
    if (paused) return undefined
    const id = setTimeout(() => onDismiss(toast.id), 5000)
    return () => clearTimeout(id)
  }, [paused, toast.id, onDismiss])

  return (
    <div
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      className="flex items-start gap-3 rounded-xl border border-line bg-surface px-4 py-3 shadow-overlay motion-safe:animate-[toast-in_200ms_ease-out]"
    >
      <CircleCheck size={20} strokeWidth={1.75} aria-hidden="true" className="mt-0.5 shrink-0 text-success" />
      <p className="flex-1 text-base text-ink">{toast.message}</p>
      <IconButton label="Dismiss" icon={X} className="size-9" onClick={() => onDismiss(toast.id)} />
    </div>
  )
}

export default function Toaster() {
  const { toasts, dismiss } = useToast()

  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 bottom-0 z-40 flex flex-col items-center gap-3 px-4 pb-4"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto w-full max-w-[26rem]">
          <Toast toast={toast} onDismiss={dismiss} />
        </div>
      ))}
    </div>
  )
}
