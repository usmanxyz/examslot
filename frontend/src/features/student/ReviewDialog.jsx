import { useId, useState } from 'react'

import Button from '../../components/ui/Button'
import Checkbox from '../../components/ui/Checkbox'
import Dialog from '../../components/ui/Dialog'
import FormAlert from '../auth/FormAlert'
import { formatDate, formatTime, formatTimeRange } from '../../lib/format'

export default function ReviewDialog({ open, onClose, branchName, picks, onSave, pending, alert }) {
  const confirmId = useId()
  const [checked, setChecked] = useState(false)
  const rows = [...picks].sort((a, b) => Date.parse(a.slot.starts_at) - Date.parse(b.slot.starts_at))

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Review your date sheet"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Keep editing
          </Button>
          <Button disabled={!checked} pending={pending} pendingLabel="Saving" onClick={onSave}>
            Save date sheet
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <p className="text-sm text-muted">{`Exam branch: ${branchName}`}</p>

        <table className="w-full border-collapse text-left text-sm">
          <caption className="sr-only">Your exams sorted by date</caption>
          <thead>
            <tr className="bg-sunken">
              <th scope="col" className="px-3 py-2 font-medium text-muted">
                Course
              </th>
              <th scope="col" className="px-3 py-2 font-medium text-muted">
                Date
              </th>
              <th scope="col" className="px-3 py-2 font-medium text-muted">
                Time
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((pick) => (
              <tr key={pick.courseId} className="border-b border-line">
                <td className="tabular px-3 py-3 font-medium text-ink">{pick.courseCode}</td>
                <td className="tabular px-3 py-3 text-ink">{formatDate(pick.slot.starts_at)}</td>
                <td className="tabular px-3 py-3 text-ink">
                  {pick.slot.end_time_set
                    ? formatTimeRange(pick.slot.starts_at, pick.slot.ends_at)
                    : formatTime(pick.slot.starts_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <p className="text-base text-ink">
          You can save your date sheet once. After that, changes need an approved request.
        </p>

        <Checkbox
          id={confirmId}
          label="I have checked my dates and times."
          checked={checked}
          onChange={(event) => setChecked(event.target.checked)}
        />

        <FormAlert message={alert} />
      </div>
    </Dialog>
  )
}
