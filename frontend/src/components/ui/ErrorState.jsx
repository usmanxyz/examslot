import { CloudOff, Lock, SearchX, ServerCrash } from 'lucide-react'

import Button from './Button'

const VARIANTS = {
  network: {
    icon: CloudOff,
    title: 'You appear to be offline',
    body: 'Check your connection and try again.',
  },
  server: {
    icon: ServerCrash,
    title: 'Something went wrong on our side',
    body: 'Try again in a moment.',
  },
  forbidden: {
    icon: Lock,
    title: 'You do not have access to this page',
    body: null,
  },
  notFound: {
    icon: SearchX,
    title: 'Page not found',
    body: 'The page you are looking for does not exist or has moved.',
  },
}

export default function ErrorState({ variant = 'server', message, onRetry, children }) {
  const entry = VARIANTS[variant]
  const Icon = entry.icon

  return (
    <div className="rounded-xl border border-line bg-surface px-6 py-10 text-center">
      <Icon size={24} strokeWidth={1.75} aria-hidden="true" className="mx-auto text-muted" />
      <p className="mt-3 text-[17px] leading-6 font-semibold text-ink">{entry.title}</p>
      {message ?? entry.body ? (
        <p className="mx-auto mt-2 max-w-[32rem] text-base text-muted">{message ?? entry.body}</p>
      ) : null}
      {onRetry || children ? (
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          {onRetry ? (
            <Button variant="secondary" onClick={onRetry}>
              Try again
            </Button>
          ) : null}
          {children}
        </div>
      ) : null}
    </div>
  )
}
