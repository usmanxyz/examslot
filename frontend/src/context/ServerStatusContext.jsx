import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'

import { createApiClient } from '../lib/api'

const ServerStatusContext = createContext(null)

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
const HEALTH_URL = BASE_URL.replace(/\/api\/v1\/?$/, '')

export function ServerStatusProvider({ children }) {
  const [slowCount, setSlowCount] = useState(0)
  const warmed = useRef(false)

  const onSlowChange = useCallback((delta) => {
    setSlowCount((current) => Math.max(0, current + delta))
  }, [])

  const publicApi = useMemo(() => createApiClient({ baseUrl: BASE_URL, onSlowChange }), [onSlowChange])

  const healthApi = useMemo(() => createApiClient({ baseUrl: HEALTH_URL }), [])

  const warmUp = useCallback(() => {
    if (warmed.current) return
    warmed.current = true
    healthApi.get('/health').catch(() => undefined)
  }, [healthApi])

  const value = useMemo(
    () => ({ slow: slowCount > 0, onSlowChange, publicApi, warmUp }),
    [slowCount, onSlowChange, publicApi, warmUp],
  )

  return <ServerStatusContext.Provider value={value}>{children}</ServerStatusContext.Provider>
}

export function useServerStatus() {
  const value = useContext(ServerStatusContext)
  if (!value) throw new Error('useServerStatus needs a ServerStatusProvider')
  return value
}
