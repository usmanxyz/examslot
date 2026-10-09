import { CalendarX } from 'lucide-react'

export default function ClashMessage({ id, message }) {
  return (
    <p id={id} className="flex items-start gap-2 text-sm text-clash">
      <CalendarX size={18} strokeWidth={1.75} aria-hidden="true" className="mt-0.5 shrink-0" />
      <span>{message}</span>
    </p>
  )
}
