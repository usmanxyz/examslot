export class ApiError extends Error {
  constructor({ status, code, message, details, retryAfterSeconds }) {
    super(message)
    this.name = 'ApiError'
    this.status = status ?? 0
    this.code = code ?? 'INTERNAL_ERROR'
    this.details = details ?? {}
    this.retryAfterSeconds = retryAfterSeconds ?? null
  }
}

export function isAborted(error) {
  return error instanceof ApiError && error.code === 'ABORTED'
}
