import { useState } from 'react'

import Button from '../../components/ui/Button'
import Dialog from '../../components/ui/Dialog'
import Field from '../../components/ui/Field'
import Textarea from '../../components/ui/Textarea'
import FormAlert from '../auth/FormAlert'
import { useMutation } from '../../hooks/useMutation'
import { formatDateTime } from '../../lib/format'

const MAX_REMARK = 500

const TYPE_LABELS = {
  branch_change: 'Branch change',
  date_sheet_change: 'Date sheet change',
}

function consequence(decision, request) {
  if (decision === 'reject') return 'Nothing changes for the student. They will see your remark.'
  return request.type === 'branch_change'
    ? `${request.student.full_name} will be able to choose a branch once more.`
    : `${request.student.full_name} will be able to change their date sheet once.`
}

export default function DecisionDialog({ open, decision, request, onClose, onDecide, onDecided }) {
  const [remark, setRemark] = useState('')
  const [error, setError] = useState(null)
  const [alert, setAlert] = useState(null)
  const { run, pending } = useMutation(onDecide)

  const onSubmit = async (event) => {
    event.preventDefault()
    setAlert(null)
    if (remark.length > MAX_REMARK) {
      setError('Use 500 characters or fewer.')
      return
    }
    const result = await run(remark.trim() ? remark.trim() : null)
    if (result.ok) {
      onDecided(result.data)
      return
    }
    setAlert(result.error?.message)
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={decision === 'approve' ? 'Approve request' : 'Reject request'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            form="decision-form"
            type="submit"
            variant={decision === 'approve' ? 'primary' : 'danger'}
            pending={pending}
            pendingLabel="Saving"
          >
            {decision === 'approve' ? 'Approve' : 'Reject'}
          </Button>
        </>
      }
    >
      <dl className="space-y-3 text-[15px] leading-6">
        <div className="flex flex-wrap gap-x-2">
          <dt className="font-medium text-ink">Student</dt>
          <dd className="text-muted">
            {request.student.full_name} <span className="tabular">{request.student.registration_no}</span>
          </dd>
        </div>
        <div className="flex flex-wrap gap-x-2">
          <dt className="font-medium text-ink">Type</dt>
          <dd className="text-muted">{TYPE_LABELS[request.type]}</dd>
        </div>
        <div className="flex flex-wrap gap-x-2">
          <dt className="font-medium text-ink">Raised</dt>
          <dd className="tabular text-muted">{formatDateTime(request.created_at)}</dd>
        </div>
        <div className="space-y-1">
          <dt className="font-medium text-ink">Reason</dt>
          <dd className="text-muted">{request.reason}</dd>
        </div>
      </dl>

      <p className="mt-5 rounded-lg bg-sunken px-3 py-2 text-[15px] leading-6 text-ink">
        {consequence(decision, request)}
      </p>

      <form id="decision-form" noValidate onSubmit={onSubmit} className="mt-5 space-y-5">
        <Field id="remark" label="Remark" optional error={error}>
          {(props) => (
            <Textarea
              {...props}
              rows={4}
              maxLength={MAX_REMARK}
              value={remark}
              onChange={(event) => setRemark(event.target.value)}
              counter={`${remark.length} of ${MAX_REMARK}`}
            />
          )}
        </Field>
        <FormAlert message={alert} />
      </form>
    </Dialog>
  )
}
