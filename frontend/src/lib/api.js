import { ApiError } from './api-error'

const TIMEOUT_MS = 75000
const SLOW_MS = 2500
const RETRY_DELAY_MS = 1500
const RETRY_STATUSES = new Set([502, 503, 504])

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function parseRetryAfter(response, details) {
  const fromDetails = Number(details?.retry_after_seconds)
  if (Number.isFinite(fromDetails) && fromDetails > 0) return fromDetails
  const header = Number(response.headers.get('Retry-After'))
  return Number.isFinite(header) && header > 0 ? header : null
}

async function toApiError(response) {
  let envelope
  try {
    envelope = await response.json()
  } catch {
    envelope = null
  }
  const error = envelope?.error ?? {}
  return new ApiError({
    status: response.status,
    code: error.code ?? 'INTERNAL_ERROR',
    message: error.message ?? 'Something went wrong on our side. Try again in a moment.',
    details: error.details ?? {},
    retryAfterSeconds: parseRetryAfter(response, error.details),
  })
}

export function createApiClient({ baseUrl, getToken, onUnauthorized, onSlowChange }) {
  async function send(method, path, { body, bodyType, signal, accept } = {}) {
    const controller = new AbortController()
    const abort = () => controller.abort(signal?.reason)
    if (signal) {
      if (signal.aborted) abort()
      else signal.addEventListener('abort', abort, { once: true })
    }
    const timeoutId = setTimeout(() => controller.abort('timeout'), TIMEOUT_MS)
    let slowCounted = false
    const slowId = setTimeout(() => {
      slowCounted = true
      onSlowChange?.(1)
    }, SLOW_MS)

    const headers = { Accept: accept ?? 'application/json' }
    const token = getToken?.()
    if (token) headers.Authorization = `Bearer ${token}`
    let payload
    if (body !== undefined) {
      if (bodyType) {
        headers['Content-Type'] = bodyType
        payload = body
      } else {
        headers['Content-Type'] = 'application/json'
        payload = JSON.stringify(body)
      }
    }

    const attempt = () => fetch(`${baseUrl}${path}`, { method, headers, body: payload, signal: controller.signal })

    const canRetry = method === 'GET'
    try {
      let response
      try {
        response = await attempt()
      } catch (cause) {
        if (controller.signal.aborted) throw cause
        if (!canRetry) throw cause
        await delay(RETRY_DELAY_MS)
        response = await attempt()
      }
      if (canRetry && RETRY_STATUSES.has(response.status)) {
        await delay(RETRY_DELAY_MS)
        response = await attempt()
      }
      if (!response.ok) {
        const error = await toApiError(response)
        if (error.status === 401 && error.code === 'UNAUTHENTICATED') onUnauthorized?.()
        throw error
      }
      return response
    } catch (cause) {
      if (cause instanceof ApiError) throw cause
      if (controller.signal.aborted) {
        const timedOut = controller.signal.reason === 'timeout'
        throw new ApiError({
          status: 0,
          code: timedOut ? 'TIMEOUT' : 'ABORTED',
          message: timedOut
            ? 'Something went wrong on our side. Try again in a moment.'
            : 'The request was cancelled.',
        })
      }
      throw new ApiError({
        status: 0,
        code: 'NETWORK_ERROR',
        message: 'Check your connection and try again.',
      })
    } finally {
      clearTimeout(timeoutId)
      clearTimeout(slowId)
      if (slowCounted) onSlowChange?.(-1)
      if (signal) signal.removeEventListener('abort', abort)
    }
  }

  async function json(method, path, options) {
    const response = await send(method, path, options)
    if (response.status === 204) return null
    const text = await response.text()
    return text ? JSON.parse(text) : null
  }

  return {
    get: (path, options) => json('GET', path, options),
    post: (path, body, options) => json('POST', path, { ...options, body }),
    put: (path, body, options) => json('PUT', path, { ...options, body }),
    patch: (path, body, options) => json('PATCH', path, { ...options, body }),
    del: (path, options) => json('DELETE', path, options),
    getBlob: async (path, options) => {
      const response = await send('GET', path, { ...options, accept: '*/*' })
      return response.blob()
    },
    putBytes: (path, bytes, type, options) =>
      json('PUT', path, { ...options, body: bytes, bodyType: type }),
  }
}
