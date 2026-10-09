import { useCallback, useEffect, useState } from 'react'

import { formatMinutesFromSeconds } from '../../lib/format'

export function useRateLimitLock() {
  const [lockedUntil, setLockedUntil] = useState(0)
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    if (lockedUntil <= now) return undefined
    const id = setTimeout(() => setNow(Date.now()), 1000)
    return () => clearTimeout(id)
  }, [lockedUntil, now])

  const lock = useCallback((seconds) => {
    const safeSeconds = Math.max(60, Math.ceil(seconds ?? 60))
    setNow(Date.now())
    setLockedUntil(Date.now() + safeSeconds * 1000)
  }, [])

  const locked = lockedUntil > now
  const message = locked
    ? `Too many attempts. Try again in ${formatMinutesFromSeconds((lockedUntil - now) / 1000)}.`
    : null

  return { locked, message, lock }
}
