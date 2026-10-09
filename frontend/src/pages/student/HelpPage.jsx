import { useCallback, useRef, useState } from 'react'

import Button from '../../components/ui/Button'
import EmptyState from '../../components/ui/EmptyState'
import ErrorState from '../../components/ui/ErrorState'
import Field from '../../components/ui/Field'
import PageHeader from '../../components/ui/PageHeader'
import RadioCard from '../../components/ui/RadioCard'
import Skeleton from '../../components/ui/Skeleton'
import StatusPill from '../../components/ui/StatusPill'
import Textarea from '../../components/ui/Textarea'
import FormAlert from '../../features/auth/FormAlert'
import { useRateLimitLock } from '../../features/auth/useRateLimitLock'
import { useStudentAuth } from '../../context/StudentAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useMutation } from '../../hooks/useMutation'
import { useQuery } from '../../hooks/useQuery'
import { createRequest, listRequests } from '../../services/student/requestService'
import { formatDateTime } from '../../lib/format'
import { validateReason } from '../../lib/validators'

const TYPES = [
  {
    value: 'branch_change',
    title: 'Request to change branch',
    description: 'Choose a different exam branch. Your exam times stay the same.',
  },
  {
    value: 'date_sheet_change',
    title: 'Request to change date sheet',
    description: 'Change the exam times you saved.',
  },
]

const MAX_REASON = 1000

function unavailableReason(type, me) {
  if (!me) return null
  if (type === 'branch_change' && !me.branch) return 'Choose your exam branch first.'
  if (type === 'date_sheet_change' && !me.date_sheet_saved_at) return 'Save your date sheet first.'
  if ((me.pending_request_types ?? []).includes(type)) {
    return 'You already have a request of this type waiting for a decision.'
  }
  return null
}

function RequestCard({ request }) {
  return (
    <li className="rounded-xl border border-line bg-surface p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[17px] leading-6 font-semibold text-ink">
          {request.type === 'branch_change' ? 'Branch change' : 'Date sheet change'}
        </p>
        <StatusPill status={request.status} />
      </div>
      <p className="mt-2 text-base text-muted">{request.reason}</p>
      <dl className="mt-3 space-y-1 text-sm text-muted">
        <div className="flex flex-wrap gap-x-2">
          <dt className="font-medium text-ink">Sent</dt>
          <dd className="tabular">{formatDateTime(request.created_at)}</dd>
        </div>
        {request.decided_at ? (
          <div className="flex flex-wrap gap-x-2">
            <dt className="font-medium text-ink">Decided</dt>
            <dd className="tabular">{formatDateTime(request.decided_at)}</dd>
          </div>
        ) : null}
        {request.admin_remark ? (
          <div className="flex flex-wrap gap-x-2">
            <dt className="font-medium text-ink">Exam office</dt>
            <dd>{request.admin_remark}</dd>
          </div>
        ) : null}
      </dl>
    </li>
  )
}

export default function HelpPage() {
  useDocumentTitle('Need help')
  const { api, me, refreshMe } = useStudentAuth()
  const { showToast } = useToast()
  const [type, setType] = useState('')
  const [reason, setReason] = useState('')
  const [errors, setErrors] = useState({})
  const [alert, setAlert] = useState(null)
  const reasonRef = useRef(null)
  const { locked, message: lockMessage, lock } = useRateLimitLock()

  const load = useCallback((signal) => listRequests(api, signal), [api])
  const { status, data, error, reload } = useQuery(load)
  const { run, pending } = useMutation((body) => createRequest(api, body))

  const onSubmit = async (event) => {
    event.preventDefault()
    setAlert(null)
    if (locked || pending) return
    const next = {
      type: type ? null : 'Choose what you need to change.',
      reason: validateReason(reason),
    }
    setErrors(next)
    if (next.type || next.reason) {
      if (next.reason && !next.type) reasonRef.current?.focus()
      return
    }
    const result = await run({ type, reason: reason.trim() })
    if (result.ok) {
      setType('')
      setReason('')
      showToast('Request sent.')
      reload()
      refreshMe().catch(() => {})
      return
    }
    const failure = result.error
    if (!failure) return
    if (failure.status === 429) {
      lock(failure.retryAfterSeconds)
      return
    }
    if (failure.status === 422) {
      const fields = failure.details?.fields ?? []
      setErrors(Object.fromEntries(fields.map((field) => [field.field, field.message])))
    }
    setAlert(failure.message)
  }

  const requests = data?.items ?? []

  return (
    <div className="space-y-10">
      <PageHeader
        title="Need help"
        meta="Ask the exam office to reopen your branch or your date sheet once."
      />

      <form noValidate onSubmit={onSubmit} className="space-y-6">
        <fieldset className="space-y-3">
          <legend className="text-sm font-medium text-ink">What needs to change</legend>
          {TYPES.map((option) => {
            const reasonText = unavailableReason(option.value, me)
            return (
              <RadioCard
                key={option.value}
                id={`request-${option.value}`}
                name="request-type"
                value={option.value}
                checked={type === option.value}
                onChange={() => {
                  setType(option.value)
                  setErrors((current) => ({ ...current, type: null }))
                }}
                title={option.title}
                description={option.description}
                unavailableReason={reasonText}
              />
            )
          })}
          {errors.type ? (
            <p role="alert" className="text-sm text-danger">
              {errors.type}
            </p>
          ) : null}
        </fieldset>

        <Field
          id="reason"
          label="Reason"
          hint="Explain what needs to change and why. 10 to 1000 characters."
          error={errors.reason}
        >
          {(props) => (
            <Textarea
              {...props}
              ref={reasonRef}
              name="reason"
              rows={5}
              maxLength={MAX_REASON}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              onBlur={() => setErrors((current) => ({ ...current, reason: validateReason(reason) }))}
              counter={`${reason.trim().length} of ${MAX_REASON}`}
            />
          )}
        </Field>

        <FormAlert message={lockMessage ?? alert} />

        <Button type="submit" pending={pending} pendingLabel="Sending" disabled={locked}>
          Send request
        </Button>
      </form>

      <section className="space-y-4">
        <h2 className="font-serif text-[22px] leading-7 font-semibold tracking-[-0.01em]">Your requests</h2>
        {status === 'loading' ? (
          <div className="space-y-3">
            <Skeleton className="h-28 w-full rounded-xl" />
            <Skeleton className="h-28 w-full rounded-xl" />
          </div>
        ) : null}
        {status === 'error' ? <ErrorState message={error?.message} onRetry={reload} /> : null}
        {status === 'success' && requests.length === 0 ? (
          <EmptyState title="No requests yet" body="Anything you send to the exam office will appear here." />
        ) : null}
        {status === 'success' && requests.length > 0 ? (
          <ul className="space-y-3">
            {requests.map((request) => (
              <RequestCard key={request.id} request={request} />
            ))}
          </ul>
        ) : null}
      </section>
    </div>
  )
}
