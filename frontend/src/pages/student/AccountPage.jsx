import { useRef, useState } from 'react'

import Button from '../../components/ui/Button'
import Field from '../../components/ui/Field'
import PageHeader from '../../components/ui/PageHeader'
import ThemeSwitcher from '../../components/ui/ThemeSwitcher'
import FormAlert from '../../features/auth/FormAlert'
import PasswordInput from '../../features/auth/PasswordInput'
import { useStudentAuth } from '../../context/StudentAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useMutation } from '../../hooks/useMutation'
import { changeStudentPassword } from '../../services/student/profileService'
import { validateConfirmation, validatePassword } from '../../lib/validators'

const HINT = 'At least 10 characters. Do not include your email address.'

function Card({ title, description, children }) {
  return (
    <section className="rounded-xl border border-line bg-surface p-6">
      <h2 className="font-serif text-[22px] leading-7 font-semibold tracking-[-0.01em]">{title}</h2>
      {description ? <p className="mt-2 text-base text-muted">{description}</p> : null}
      <div className="mt-6">{children}</div>
    </section>
  )
}

export default function AccountPage() {
  useDocumentTitle('Account')
  const { api, me, signOut, adoptSession } = useStudentAuth()
  const { showToast } = useToast()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [errors, setErrors] = useState({})
  const [alert, setAlert] = useState(null)
  const currentRef = useRef(null)
  const { run, pending } = useMutation((body) => changeStudentPassword(api, body))

  const onSubmit = async (event) => {
    event.preventDefault()
    setAlert(null)
    if (pending) return
    const next = {
      current_password: currentPassword ? null : 'Your current password is required.',
      new_password: validatePassword(newPassword, me?.email),
      confirmation: validateConfirmation(confirmation, newPassword),
    }
    setErrors(next)
    if (next.current_password || next.new_password || next.confirmation) {
      if (next.current_password) currentRef.current?.focus()
      return
    }
    const result = await run({ current_password: currentPassword, new_password: newPassword })
    if (result.ok) {
      adoptSession(result.data)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmation('')
      showToast('Password changed. Other devices have been signed out.')
      return
    }
    const failure = result.error
    if (!failure) return
    if (failure.code === 'CURRENT_PASSWORD_INCORRECT') {
      setErrors({ current_password: failure.message })
      currentRef.current?.focus()
      return
    }
    if (failure.code === 'PASSWORD_TOO_WEAK') {
      setErrors({ new_password: failure.message })
      return
    }
    if (failure.status === 422) {
      const fields = failure.details?.fields ?? []
      setErrors(Object.fromEntries(fields.map((field) => [field.field, field.message])))
    }
    setAlert(failure.message)
  }

  return (
    <div className="space-y-8">
      <PageHeader title="Account" meta={me?.email} />

      <Card title="Change password" description="You stay signed in here. Every other session ends.">
        <form noValidate onSubmit={onSubmit} className="max-w-[30rem] space-y-6">
          <Field id="current-password" label="Current password" error={errors.current_password}>
            {(props) => (
              <PasswordInput
                {...props}
                ref={currentRef}
                name="current_password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
              />
            )}
          </Field>

          <Field id="new-password" label="New password" hint={HINT} error={errors.new_password}>
            {(props) => (
              <PasswordInput
                {...props}
                name="new_password"
                autoComplete="new-password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                onBlur={() =>
                  setErrors((current) => ({
                    ...current,
                    new_password: validatePassword(newPassword, me?.email),
                  }))
                }
              />
            )}
          </Field>

          <Field id="confirmation" label="Confirm new password" error={errors.confirmation}>
            {(props) => (
              <PasswordInput
                {...props}
                name="confirmation"
                autoComplete="new-password"
                value={confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
                onBlur={() =>
                  setErrors((current) => ({
                    ...current,
                    confirmation: validateConfirmation(confirmation, newPassword),
                  }))
                }
              />
            )}
          </Field>

          <FormAlert message={alert} />

          <Button type="submit" pending={pending} pendingLabel="Saving">
            Change password
          </Button>
        </form>
      </Card>

      <Card title="Appearance" description="ExamSlot keeps this choice in your browser.">
        <div className="max-w-[20rem]">
          <ThemeSwitcher />
        </div>
      </Card>

      <Card title="Sign out" description="You will need your password to sign in again.">
        <Button variant="secondary" onClick={signOut}>
          Sign out
        </Button>
      </Card>
    </div>
  )
}
