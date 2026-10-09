import { useCallback, useRef, useState } from 'react'

import { isAborted } from '../lib/api-error'

export function useMutation(fn) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState(null)
  const inFlight = useRef(false)

  const run = useCallback(
    async (...args) => {
      if (inFlight.current) return { ok: false, error: null }
      inFlight.current = true
      setPending(true)
      setError(null)
      try {
        const data = await fn(...args)
        return { ok: true, data }
      } catch (cause) {
        if (!isAborted(cause)) setError(cause)
        return { ok: false, error: cause }
      } finally {
        inFlight.current = false
        setPending(false)
      }
    },
    [fn],
  )

  const reset = useCallback(() => setError(null), [])

  return { run, pending, error, reset }
}
