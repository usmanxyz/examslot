import { useId } from 'react'

import { useTheme } from '../../context/ThemeContext'

const OPTIONS = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' },
]

export default function ThemeSwitcher() {
  const { preference, setPreference } = useTheme()
  const name = useId()

  return (
    <fieldset>
      <legend className="text-sm font-medium text-muted">Theme</legend>
      <div className="mt-2 flex gap-1 rounded-lg border border-line bg-surface p-1">
        {OPTIONS.map((option) => (
          <label
            key={option.value}
            className={`flex min-h-9 flex-1 cursor-pointer items-center justify-center rounded-md px-3 text-sm font-medium transition-colors duration-120 ${
              preference === option.value ? 'bg-primary-soft text-primary' : 'text-muted hover:bg-sunken'
            }`}
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={preference === option.value}
              onChange={() => setPreference(option.value)}
              className="sr-only"
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}
