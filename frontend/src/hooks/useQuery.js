import { useCallback, useEffect, useState } from 'react'

import { isAborted } from '../lib/api-error'

const LOADING = { status: 'loading', data: null, error: null }

export function useQuery(fn) {
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState(LOADING)

  useEffect(() => {
    const controller = new AbortController()
    let live = true
    fn(controller.signal)
      .then((data) => {
        if (live) setState({ status: 'success', data, error: null })
      })
      .catch((error) => {
        if (!live || isAborted(error)) return
        setState({ status: 'error', data: null, error })
      })
    return () => {
      live = false
      controller.abort()
    }
  }, [fn, attempt])

  const reload = useCallback(() => {
    setState(LOADING)
    setAttempt((value) => value + 1)
  }, [])

  return { ...state, reload }
}
