import { useServerStatus } from '../../context/ServerStatusContext'

export default function ServerWakeNotice() {
  const { slow } = useServerStatus()

  return (
    <div aria-live="polite" className="fixed inset-x-0 top-0 z-30 flex justify-center px-4">
      {slow ? (
        <p className="mt-3 rounded-xl border border-line bg-warning-soft px-4 py-3 text-sm text-warning shadow-overlay">
          Waking the server. The first request after a quiet period can take up to a minute.
        </p>
      ) : null}
    </div>
  )
}
