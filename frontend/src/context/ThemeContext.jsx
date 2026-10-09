import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { readStoredText, THEME_KEY, writeStoredText } from '../lib/storage'

const ThemeContext = createContext(null)

const PREFERENCES = ['light', 'dark', 'system']

function readPreference() {
  const stored = readStoredText(window.localStorage, THEME_KEY)
  return PREFERENCES.includes(stored) ? stored : 'system'
}

function systemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({ children }) {
  const [preference, setPreferenceState] = useState(readPreference)
  const [system, setSystem] = useState(systemTheme)

  useEffect(() => {
    if (preference !== 'system') return undefined
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const listen = (event) => setSystem(event.matches ? 'dark' : 'light')
    media.addEventListener('change', listen)
    return () => media.removeEventListener('change', listen)
  }, [preference])

  const theme = preference === 'system' ? system : preference

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  const setPreference = useCallback((next) => {
    setPreferenceState(next)
    writeStoredText(window.localStorage, THEME_KEY, next)
  }, [])

  const value = useMemo(() => ({ preference, theme, setPreference }), [preference, theme, setPreference])

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const value = useContext(ThemeContext)
  if (!value) throw new Error('useTheme needs a ThemeProvider')
  return value
}
