import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'

import { useServerStatus } from './ServerStatusContext'
import { createApiClient } from '../lib/api'
import { isAborted } from '../lib/api-error'
import { readStored, removeStored, STUDENT_SESSION_KEY, writeStored } from '../lib/storage'
import { studentLogin, studentLogout } from '../services/authService'
import { getMe } from '../services/student/profileService'

const StudentAuthContext = createContext(null)

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
const SESSION_ENDED = 'Your session has ended. Sign in again.'

function readSession() {
  const stored = readStored(window.sessionStorage, STUDENT_SESSION_KEY)
  if (!stored?.token || !stored?.expiresAt) return null
  return Date.parse(stored.expiresAt) > Date.now() ? stored : null
}

export function StudentAuthProvider({ children }) {
  const navigate = useNavigate()
  const { onSlowChange } = useServerStatus()
  const [session, setSession] = useState(readSession)
  const [me, setMe] = useState(null)
  const [status, setStatus] = useState(() => (readSession() ? 'loading' : 'signedOut'))

  const clearSession = useCallback(() => {
    removeStored(window.sessionStorage, STUDENT_SESSION_KEY)
    setSession(null)
    setMe(null)
    setStatus('signedOut')
  }, [])

  const endSession = useCallback(() => {
    clearSession()
    navigate('/login', { replace: true, state: { notice: SESSION_ENDED } })
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
    if (!token || me) return undefined
    const controller = new AbortController()
    getMe(api, controller.signal)
      .then((profile) => {
        setMe(profile)
        setStatus('signedIn')
      })
      .catch((error) => {
        if (isAborted(error)) return
        setStatus('signedOut')
      })
    return () => controller.abort()
  }, [token, me, api])

  const signIn = useCallback(async (email, password) => {
    const anonymous = createApiClient({ baseUrl: BASE_URL, onSlowChange })
    const result = await studentLogin(anonymous, { email, password })
    const next = {
      token: result.access_token,
      expiresAt: new Date(Date.now() + result.expires_in * 1000).toISOString(),
    }
    writeStored(window.sessionStorage, STUDENT_SESSION_KEY, next)
    setStatus('loading')
    setMe(null)
    setSession(next)
  }, [onSlowChange])

  const signOut = useCallback(async () => {
    try {
      await studentLogout(api)
    } catch {
      removeStored(window.sessionStorage, STUDENT_SESSION_KEY)
    }
    clearSession()
    navigate('/login', { replace: true })
  }, [api, clearSession, navigate])

  const refreshMe = useCallback(async () => {
    const profile = await getMe(api)
    setMe(profile)
    setStatus('signedIn')
    return profile
  }, [api])

  const value = useMemo(
    () => ({ api, me, status, signIn, signOut, refreshMe }),
    [api, me, status, signIn, signOut, refreshMe],
  )

  return <StudentAuthContext.Provider value={value}>{children}</StudentAuthContext.Provider>
}

export function useStudentAuth() {
  const value = useContext(StudentAuthContext)
  if (!value) throw new Error('useStudentAuth needs a StudentAuthProvider')
  return value
}
