export function readStored(storage, key) {
  try {
    const raw = storage.getItem(key)
    return raw === null ? null : JSON.parse(raw)
  } catch {
    return null
  }
}

export function writeStored(storage, key, value) {
  try {
    storage.setItem(key, JSON.stringify(value))
  } catch {
    return
  }
}

export function removeStored(storage, key) {
  try {
    storage.removeItem(key)
  } catch {
    return
  }
}

export const THEME_KEY = 'examslot.theme'
export const STUDENT_SESSION_KEY = 'examslot.student'
export const PLANNER_DRAFT_KEY = 'examslot.plannerDraft'

export function readStoredText(storage, key) {
  try {
    return storage.getItem(key)
  } catch {
    return null
  }
}

export function writeStoredText(storage, key, value) {
  try {
    storage.setItem(key, value)
  } catch {
    return
  }
}
