import { CircleAlert } from 'lucide-react'

export default function FormAlert({ message }) {
  if (!message) return null

  return (
    <p role="alert" className="flex items-start gap-2 rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">
      <CircleAlert size={18} strokeWidth={1.75} aria-hidden="true" className="mt-0.5 shrink-0" />
      <span>{message}</span>
    </p>
  )
}
