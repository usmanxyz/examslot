import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import Button from '../../components/ui/Button'
import Field from '../../components/ui/Field'
import TextInput from '../../components/ui/TextInput'
import FormAlert from '../../features/auth/FormAlert'
import PasswordInput from '../../features/auth/PasswordInput'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useServerStatus } from '../../context/ServerStatusContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useMutation } from '../../hooks/useMutation'

export default function AdminLoginPage() {
  useDocumentTitle('Admin sign in')
  const { warmUp } = useServerStatus()
  const { signIn, status } = useAdminAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [alert, setAlert] = useState(null)
  const { run, pending } = useMutation((values) => signIn(values.email, values.password))

  useEffect(() => {
    warmUp()
  }, [warmUp])

  useEffect(() => {
    if (status === 'signedIn') navigate('/admin', { replace: true })
  }, [status, navigate])

  const onSubmit = async (event) => {
    event.preventDefault()
    setAlert(null)
    const result = await run({ email: email.trim(), password })
    if (!result.ok && result.error) setAlert(result.error.message)
  }

  return (
    <div className="mx-auto w-full max-w-[30rem] pt-10 pb-14 sm:pt-20">
      <h1 className="font-serif text-[28px] leading-9 font-semibold tracking-[-0.01em] sm:text-[34px] sm:leading-[42px]">
        Admin sign in
      </h1>
      <p className="mt-2 text-base text-muted">For exam office staff.</p>

      <form noValidate onSubmit={onSubmit} className="mt-8 space-y-6">
        <Field id="admin-email" label="Email">
          {(props) => (
            <TextInput
              {...props}
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          )}
        </Field>

        <Field id="admin-password" label="Password">
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

        <FormAlert message={alert} />

        <Button type="submit" className="w-full" pending={pending} pendingLabel="Signing in">
          Sign in
        </Button>
      </form>

      <p className="mt-8 text-sm text-muted">
        <Link to="/login" className="text-primary">
          Student sign in
        </Link>
      </p>
    </div>
  )
}
