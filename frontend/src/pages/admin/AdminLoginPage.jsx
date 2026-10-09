import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'

import Button from '../../components/ui/Button'
import Field from '../../components/ui/Field'
import TextInput from '../../components/ui/TextInput'
import FormAlert from '../../features/auth/FormAlert'
import PasswordInput from '../../features/auth/PasswordInput'
import { useRateLimitLock } from '../../features/auth/useRateLimitLock'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useServerStatus } from '../../context/ServerStatusContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useMutation } from '../../hooks/useMutation'
import { validateEmail } from '../../lib/validators'

export default function AdminLoginPage() {
  useDocumentTitle('Admin sign in')
  const { warmUp } = useServerStatus()
  const { signIn } = useAdminAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const notice = location.state?.notice ?? null

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [alert, setAlert] = useState(null)
  const emailRef = useRef(null)
  const { locked, message: lockMessage, lock } = useRateLimitLock()
  const { run, pending } = useMutation((values) => signIn(values.email, values.password))

  useEffect(() => {
    warmUp()
  }, [warmUp])

  const onSubmit = async (event) => {
    event.preventDefault()
    setAlert(null)
    if (locked || pending) return
    const next = {
      email: validateEmail(email),
      password: password ? null : 'Password is required.',
    }
    setErrors(next)
    if (next.email || next.password) {
      if (next.email) emailRef.current?.focus()
      return
    }
    const result = await run({ email: email.trim(), password })
    if (result.ok) {
      navigate('/admin', { replace: true })
      return
    }
    const error = result.error
    if (!error) return
    if (error.status === 429) {
      lock(error.retryAfterSeconds)
      return
    }
    if (error.status === 422) {
      const fields = error.details?.fields ?? []
      setErrors(Object.fromEntries(fields.map((field) => [field.field, field.message])))
    }
    setAlert(error.message)
  }

  return (
    <div className="mx-auto w-full max-w-[30rem] pt-10 pb-14 sm:pt-20">
      <h1 className="font-serif text-[28px] leading-9 font-semibold tracking-[-0.01em] sm:text-[34px] sm:leading-[42px]">
        Admin sign in
      </h1>
      <p className="mt-2 text-base text-muted">For exam office staff.</p>

      {notice ? (
        <p role="status" className="mt-6 rounded-lg bg-warning-soft px-3 py-2 text-sm text-warning">
          {notice}
        </p>
      ) : null}

      <form noValidate onSubmit={onSubmit} className="mt-8 space-y-6">
        <Field id="email" label="Email" error={errors.email}>
          {(props) => (
            <TextInput
              {...props}
              ref={emailRef}
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          )}
        </Field>

        <Field id="password" label="Password" error={errors.password}>
          {(props) => (
            <PasswordInput
              {...props}
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          )}
        </Field>

        <FormAlert message={lockMessage ?? alert} />

        <Button type="submit" className="w-full" pending={pending} pendingLabel="Signing in" disabled={locked}>
          Sign in
        </Button>
      </form>

      <p className="mt-8 text-sm text-muted">
        Students:{' '}
        <Link to="/login" className="text-primary">
          sign in here
        </Link>
        .
      </p>
    </div>
  )
}
