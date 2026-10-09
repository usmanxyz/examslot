const CNIC_DIGITS = /^\d{13}$/
const MOBILE = /^(?:\+92|0092|92|0)?3\d{9}$/
const GENERAL_PHONE = /^(?:\+92|0092|92|0)?\d{9,11}$/
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

export function digitsOnly(value) {
  return String(value ?? '').replace(/\D/g, '')
}

export function required(value, label) {
  return String(value ?? '').trim() ? null : `${label} is required.`
}

export function validateEmail(value) {
  const email = String(value ?? '').trim()
  if (!email) return 'Email is required.'
  if (!EMAIL.test(email)) return 'Enter a valid email address.'
  if (email.length > 254) return 'Use 254 characters or fewer.'
  return null
}

export function validateCnic(value) {
  const digits = digitsOnly(value)
  if (!digits) return 'CNIC or B-Form number is required.'
  return CNIC_DIGITS.test(digits) ? null : 'Enter 13 digits, for example 00000-0000000-1.'
}

export function validateMobile(value) {
  const raw = String(value ?? '').replace(/[\s-]/g, '')
  if (!raw) return 'Mobile number is required.'
  return MOBILE.test(raw) ? null : 'Enter a Pakistani mobile number, for example 0300 0000201.'
}

export function validatePhone(value) {
  const raw = String(value ?? '').replace(/[\s-]/g, '')
  if (!raw) return 'Phone number is required.'
  return GENERAL_PHONE.test(raw) ? null : 'Enter a Pakistani phone number.'
}

export function validateLength(value, label, min, max) {
  const text = String(value ?? '').trim()
  if (text.length < min) return `${label} needs at least ${min} characters.`
  if (text.length > max) return `${label} can be at most ${max} characters.`
  return null
}

export function validateRange(value, label, min, max) {
  const number = Number(value)
  if (!Number.isFinite(number)) return `${label} must be a number.`
  if (number < min || number > max) return `${label} must be between ${min} and ${max}.`
  return null
}

export function validatePassword(value, email) {
  const password = String(value ?? '')
  if (!password) return 'New password is required.'
  if (password.length < 10) return 'Use at least 10 characters, and do not include your email address.'
  if (password.length > 128) return 'Use 128 characters or fewer.'
  const trimmedEmail = String(email ?? '').trim().toLowerCase()
  if (trimmedEmail && password.toLowerCase().includes(trimmedEmail)) {
    return 'Use at least 10 characters, and do not include your email address.'
  }
  const local = trimmedEmail.split('@')[0]
  if (local && local.length > 2 && password.toLowerCase().includes(local)) {
    return 'Use at least 10 characters, and do not include your email address.'
  }
  return null
}

export function validateConfirmation(value, password) {
  if (!String(value ?? '')) return 'Confirm your password.'
  return value === password ? null : 'Both passwords must match.'
}

export function validateReason(value) {
  const text = String(value ?? '').trim()
  if (text.length < 10) return 'Give at least 10 characters so the exam office can judge the request.'
  if (text.length > 1000) return 'Use 1000 characters or fewer.'
  return null
}

export function firstError(errors) {
  return Object.keys(errors).find((key) => errors[key]) ?? null
}
