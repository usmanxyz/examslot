import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'

import { useServerStatus } from './ServerStatusContext'
import { createApiClient } from '../lib/api'
import { isAborted } from '../lib/api-error'
import { ADMIN_SESSION_KEY, readStored, removeStored, writeStored } from '../lib/storage'
import { adminLogin, adminLogout } from '../services/authService'
import { getAdmin } from '../services/admin/accountService'

const AdminAuthContext = createContext(null)

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
const SESSION_ENDED = 'Your session has ended. Sign in again.'

function readSession() {
  const stored = readStored(window.sessionStorage, ADMIN_SESSION_KEY)
  if (!stored?.token || !stored?.expiresAt) return null
  return Date.parse(stored.expiresAt) > Date.now() ? stored : null
}

export function AdminAuthProvider({ children }) {
  const navigate = useNavigate()
  const { onSlowChange } = useServerStatus()
  const [session, setSession] = useState(readSession)
  const [admin, setAdmin] = useState(null)
  const [status, setStatus] = useState(() => (readSession() ? 'loading' : 'signedOut'))

  const clearSession = useCallback(() => {
    removeStored(window.sessionStorage, ADMIN_SESSION_KEY)
    setSession(null)
    setAdmin(null)
    setStatus('signedOut')
  }, [])

  const endSession = useCallback(() => {
    clearSession()
    navigate('/admin/login', { replace: true, state: { notice: SESSION_ENDED } })
  }, [clearSession, navigate])

  const token = session?.token ?? null

  const api = useMemo(
    () =>
      createApiClient({
        baseUrl: BASE_URL,
        getToken: () => token,
        onUnauthorized: endSession,
        onSlowChange,
      }),
    [token, endSession, onSlowChange],
  )

  useEffect(() => {
    if (!session) return undefined
    const remaining = Date.parse(session.expiresAt) - Date.now()
    const id = setTimeout(endSession, Math.max(0, remaining))
    return () => clearTimeout(id)
  }, [session, endSession])

  useEffect(() => {
    if (!token || admin) return undefined
    const controller = new AbortController()
    getAdmin(api, controller.signal)
      .then((profile) => {
        setAdmin(profile)
        setStatus('signedIn')
      })
      .catch((error) => {
        if (isAborted(error)) return
        setStatus('signedOut')
      })
    return () => controller.abort()
  }, [token, admin, api])

  const signIn = useCallback(
    async (email, password) => {
      const anonymous = createApiClient({ baseUrl: BASE_URL, onSlowChange })
      const result = await adminLogin(anonymous, { email, password })
      const next = {
        token: result.access_token,
        expiresAt: new Date(Date.now() + result.expires_in * 1000).toISOString(),
      }
      writeStored(window.sessionStorage, ADMIN_SESSION_KEY, next)
      setStatus('loading')
      setAdmin(null)
      setSession(next)
    },
    [onSlowChange],
  )

  const signOut = useCallback(async () => {
    try {
      await adminLogout(api)
    } catch {
      removeStored(window.sessionStorage, ADMIN_SESSION_KEY)
    }
    clearSession()
    navigate('/admin/login', { replace: true })
  }, [api, clearSession, navigate])

  const value = useMemo(
    () => ({ api, admin, status, signIn, signOut }),
    [api, admin, status, signIn, signOut],
  )

  return <AdminAuthContext.Provider value={value}>{children}</AdminAuthContext.Provider>
}

export function useAdminAuth() {
  const value = useContext(AdminAuthContext)
  if (!value) throw new Error('useAdminAuth needs an AdminAuthProvider')
  return value
}
