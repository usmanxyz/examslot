const ZONE = 'Asia/Karachi'

function parts(value, options) {
  return new Intl.DateTimeFormat('en-GB', { timeZone: ZONE, ...options }).formatToParts(new Date(value))
}

function pick(list, type) {
  return list.find((part) => part.type === type)?.value ?? ''
}

export function formatDate(value) {
  const list = parts(value, { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })
  return `${pick(list, 'weekday')} ${pick(list, 'day')} ${pick(list, 'month')} ${pick(list, 'year')}`
}

export function formatDateShort(value) {
  const list = parts(value, { day: '2-digit', month: 'short', year: 'numeric' })
  return `${pick(list, 'day')} ${pick(list, 'month')} ${pick(list, 'year')}`
}

export function formatDateWithoutYear(value) {
  const list = parts(value, { weekday: 'short', day: '2-digit', month: 'short' })
  return `${pick(list, 'weekday')} ${pick(list, 'day')} ${pick(list, 'month')}`
}

export function formatYear(value) {
  return pick(parts(value, { year: 'numeric' }), 'year')
}

export function formatTime(value) {
  const list = parts(value, { hour: '2-digit', minute: '2-digit', hour12: true })
  return `${pick(list, 'hour')}:${pick(list, 'minute')} ${pick(list, 'dayPeriod').toUpperCase()}`
}

export function formatDateTime(value) {
  return `${formatDate(value)} at ${formatTime(value)}`
}

export function formatTimeRange(startsAt, endsAt) {
  return `${formatTime(startsAt)} to ${formatTime(endsAt)}`
}

export function formatClockTime(clock) {
  const [hour, minute] = clock.split(':').map(Number)
  const period = hour < 12 ? 'AM' : 'PM'
  const display = hour % 12 === 0 ? 12 : hour % 12
  return `${String(display).padStart(2, '0')}:${String(minute).padStart(2, '0')} ${period}`
}

export function formatCnic(value) {
  const digits = String(value ?? '').replace(/\D/g, '')
  if (digits.length !== 13) return String(value ?? '')
  return `${digits.slice(0, 5)}-${digits.slice(5, 12)}-${digits.slice(12)}`
}

export function formatPhone(value) {
  const raw = String(value ?? '')
  const match = raw.match(/^\+92(3\d{2})(\d{7})$/)
  if (!match) return raw
  return `+92 ${match[1]} ${match[2]}`
}

export function formatScore(type, score) {
  return type === 'cgpa' ? `${score} CGPA` : `${score} percent`
}

export function formatMinutesFromSeconds(seconds) {
  const minutes = Math.max(1, Math.ceil((seconds ?? 60) / 60))
  return minutes === 1 ? '1 minute' : `${minutes} minutes`
}

export function titleCase(value) {
  return String(value ?? '')
    .split('_')
    .map((word) => (word ? word[0].toUpperCase() + word.slice(1) : word))
    .join(' ')
}
