import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import Button from '../../components/ui/Button'
import ErrorState from '../../components/ui/ErrorState'
import Field from '../../components/ui/Field'
import Skeleton from '../../components/ui/Skeleton'
import FormAlert from '../../features/auth/FormAlert'
import PasswordInput from '../../features/auth/PasswordInput'
import { useRateLimitLock } from '../../features/auth/useRateLimitLock'
import { useServerStatus } from '../../context/ServerStatusContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useMutation } from '../../hooks/useMutation'
import { useQuery } from '../../hooks/useQuery'
import { setPassword, verifyLink } from '../../services/authService'
import { formatDateWithoutYear, formatTime } from '../../lib/format'
import { validateConfirmation, validatePassword } from '../../lib/validators'

const HINT = 'At least 10 characters. Do not include your email address.'

function readTokenFromHash() {
  const hash = window.location.hash.replace(/^#/, '')
  const token = new URLSearchParams(hash).get('token')
  if (token) {
    window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`)
  }
  return token
}

export default function SetPasswordPage() {
  useDocumentTitle('Set your password')
  const navigate = useNavigate()
  const { publicApi, warmUp } = useServerStatus()
  const [token] = useState(readTokenFromHash)
  const [password, setPasswordValue] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [errors, setErrors] = useState({})
  const [alert, setAlert] = useState(null)
  const [done, setDone] = useState(false)
  const { locked, message: lockMessage, lock } = useRateLimitLock()

  useEffect(() => {
    warmUp()
  }, [warmUp])

  const load = useCallback(
    (signal) => (token ? verifyLink(publicApi, token, signal) : Promise.resolve(null)),
    [publicApi, token],
  )
  const link = useQuery(load)
  const { run, pending } = useMutation(() => setPassword(publicApi, token, password))

  const invalid =
    !token || link.data === null || (link.status === 'error' && link.error?.status === 400)

  const validate = () => {
    const next = {
      password: validatePassword(password),
      confirmation: validateConfirmation(confirmation, password),
    }
    setErrors(next)
    return !next.password && !next.confirmation
  }

  const onSubmit = async (event) => {
    event.preventDefault()
    setAlert(null)
    if (locked || pending) return
    if (!validate()) return
    const result = await run()
    if (result.ok) {
      setDone(true)
      return
    }
    const error = result.error
    if (!error) return
    if (error.status === 429) {
      lock(error.retryAfterSeconds)
      return
    }
    if (error.status === 422 && error.code === 'PASSWORD_TOO_WEAK') {
      setErrors({ password: error.message })
      return
    }
    if (error.status === 422) {
      const fields = error.details?.fields ?? []
      setErrors(Object.fromEntries(fields.map((field) => [field.field, field.message])))
      setAlert(error.message)
      return
    }
    setAlert(error.message)
  }

  if (link.status === 'loading') {
    return (
      <div aria-busy="true" className="mx-auto w-full max-w-[30rem] space-y-6 pt-10 pb-14 sm:pt-20">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-5 w-80" />
        <Skeleton className="h-11 w-full" />
        <Skeleton className="h-11 w-full" />
        <Skeleton className="h-11 w-full" />
      </div>
    )
  }

  if (link.status === 'error' && !invalid) {
    const variant = link.error?.code === 'NETWORK_ERROR' ? 'network' : 'server'
    return (
      <div className="mx-auto w-full max-w-[30rem] pt-10 pb-14 sm:pt-20">
        <ErrorState variant={variant} onRetry={link.reload} />
      </div>
    )
  }

  if (invalid) {
    return (
      <div className="mx-auto w-full max-w-[30rem] pt-10 pb-14 sm:pt-20">
        <h1 className="font-serif text-[28px] leading-9 font-semibold tracking-[-0.01em] sm:text-[34px] sm:leading-[42px]">
          This link is no longer valid
        </h1>
        <p className="mt-2 text-base text-muted">
          Links work once and expire. Request a new one and use the newest email.
        </p>
        <Button className="mt-8" onClick={() => navigate('/forgot-password')}>
          Request a new link
        </Button>
      </div>
    )
  }

  if (done) {
    return (
      <div className="mx-auto w-full max-w-[30rem] pt-10 pb-14 sm:pt-20">
        <h1 className="font-serif text-[28px] leading-9 font-semibold tracking-[-0.01em] sm:text-[34px] sm:leading-[42px]">
          Your password is set.
        </h1>
        <p className="mt-2 text-base text-muted">Sign in with your email and new password.</p>
        <Button className="mt-8" onClick={() => navigate('/login')}>
          Sign in
        </Button>
      </div>
    )
  }

  const setup = link.data.purpose === 'setup'

  return (
    <div className="mx-auto w-full max-w-[30rem] pt-10 pb-14 sm:pt-20">
      <h1 className="font-serif text-[28px] leading-9 font-semibold tracking-[-0.01em] sm:text-[34px] sm:leading-[42px]">
        {setup ? 'Set your password' : 'Choose a new password'}
      </h1>
      <p className="tabular mt-2 text-base text-muted">
        {`This link works until ${formatDateWithoutYear(link.data.expires_at)}, ${formatTime(link.data.expires_at)}.`}
      </p>

      <form noValidate onSubmit={onSubmit} className="mt-8 space-y-6">
        <Field id="new-password" label="New password" hint={HINT} error={errors.password}>
          {(props) => (
            <PasswordInput
              {...props}
              name="new-password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPasswordValue(event.target.value)}
              onBlur={() =>
                setErrors((current) => ({ ...current, password: validatePassword(password) }))
              }
            />
          )}
        </Field>

        <Field id="confirm-password" label="Confirm password" error={errors.confirmation}>
          {(props) => (
            <PasswordInput
              {...props}
              name="confirm-password"
              autoComplete="new-password"
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              onBlur={() =>
                setErrors((current) => ({
                  ...current,
                  confirmation: validateConfirmation(confirmation, password),
                }))
              }
            />
          )}
        </Field>

        <FormAlert message={lockMessage ?? alert} />

        <Button type="submit" className="w-full" pending={pending} pendingLabel="Saving" disabled={locked}>
          Set password
        </Button>
      </form>

      <p className="mt-8 text-sm text-muted">
        <Link to="/login" className="text-primary">
          Back to sign in
        </Link>
      </p>
    </div>
  )
}
