import { useRef, useState } from 'react'
import { Link } from 'react-router'
import { MailCheck } from 'lucide-react'

import Button from '../../components/ui/Button'
import Field from '../../components/ui/Field'
import TextInput from '../../components/ui/TextInput'
import FormAlert from '../../features/auth/FormAlert'
import { useRateLimitLock } from '../../features/auth/useRateLimitLock'
import { useServerStatus } from '../../context/ServerStatusContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useMutation } from '../../hooks/useMutation'
import { forgotPassword } from '../../services/authService'
import { validateEmail } from '../../lib/validators'

export default function ForgotPasswordPage() {
  useDocumentTitle('Forgot your password')
  const { publicApi } = useServerStatus()
  const [email, setEmail] = useState('')
  const [error, setError] = useState(null)
  const [alert, setAlert] = useState(null)
  const [sent, setSent] = useState(null)
  const emailRef = useRef(null)
  const { locked, message: lockMessage, lock } = useRateLimitLock()
  const { run, pending } = useMutation((value) => forgotPassword(publicApi, value))

  const onSubmit = async (event) => {
    event.preventDefault()
    setAlert(null)
    if (locked || pending) return
    const emailError = validateEmail(email)
    setError(emailError)
    if (emailError) {
      emailRef.current?.focus()
      return
    }
    const result = await run(email.trim())
    if (result.ok) {
      setSent(result.data.message)
      return
    }
    const failure = result.error
    if (!failure) return
    if (failure.status === 429) {
      lock(failure.retryAfterSeconds)
      return
    }
    setAlert(failure.message)
  }

  if (sent) {
    return (
      <div className="mx-auto w-full max-w-[30rem] pt-10 pb-14 sm:pt-20">
        <MailCheck size={24} strokeWidth={1.75} aria-hidden="true" className="text-primary" />
        <h1 className="mt-3 font-serif text-[28px] leading-9 font-semibold tracking-[-0.01em] sm:text-[34px] sm:leading-[42px]">
          Check your email
        </h1>
        <p role="status" className="mt-2 text-base text-muted">
          {sent}
        </p>
        <Link to="/login" className="mt-8 inline-flex min-h-11 items-center text-base text-primary">
          Back to sign in
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto w-full max-w-[30rem] pt-10 pb-14 sm:pt-20">
      <h1 className="font-serif text-[28px] leading-9 font-semibold tracking-[-0.01em] sm:text-[34px] sm:leading-[42px]">
        Forgot your password
      </h1>
      <p className="mt-2 text-base text-muted">
        Enter the email your exam office registered for you and we will send a link to set a new password.
      </p>

      <form noValidate onSubmit={onSubmit} className="mt-8 space-y-6">
        <Field id="email" label="Email" error={error}>
          {(props) => (
            <TextInput
              {...props}
              ref={emailRef}
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              onBlur={() => setError(validateEmail(email))}
            />
          )}
        </Field>

        <FormAlert message={lockMessage ?? alert} />

        <Button type="submit" className="w-full" pending={pending} pendingLabel="Sending" disabled={locked}>
          Send the link
        </Button>

        <Link to="/login" className="inline-flex min-h-11 items-center text-base text-primary">
          Back to sign in
        </Link>
      </form>
    </div>
  )
}
