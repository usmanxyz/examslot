import { useState } from 'react'

import Button from '../../components/ui/Button'
import Dialog from '../../components/ui/Dialog'
import Field from '../../components/ui/Field'
import Select from '../../components/ui/Select'
import TextInput from '../../components/ui/TextInput'
import FormAlert from '../auth/FormAlert'
import { useMutation } from '../../hooks/useMutation'
import { required } from '../../lib/validators'

function initialValues(slot) {
  if (!slot) return { course_id: '', date: '', start_time: '', end_time: '', seats_per_branch: '40' }
  return {
    course_id: slot.course.id,
    date: slot.date,
    start_time: slot.start_time,
    end_time: slot.end_time_set ? slot.end_time : '',
    seats_per_branch: String(slot.seats_per_branch),
  }
}

export default function SlotDialog({ open, slot, courses, onClose, onSave, onSaved }) {
  const [values, setValues] = useState(() => initialValues(slot))
  const [errors, setErrors] = useState({})
  const [alert, setAlert] = useState(null)
  const { run, pending } = useMutation(onSave)
  const timesLocked = Boolean(slot && slot.chosen_count > 0)

  const setValue = (key) => (event) => setValues((current) => ({ ...current, [key]: event.target.value }))

  const onSubmit = async (event) => {
    event.preventDefault()
    setAlert(null)
    const next = timesLocked
      ? {}
      : {
          course_id: slot ? null : required(values.course_id, 'Course'),
          date: required(values.date, 'Date'),
          start_time: required(values.start_time, 'Start time'),
        }
    const seats = Number(values.seats_per_branch)
    next.seats_per_branch =
      Number.isInteger(seats) && seats >= 1 && seats <= 1000 ? null : 'Seats must be between 1 and 1000.'
    setErrors(next)
    if (Object.values(next).some(Boolean)) return

    const body = timesLocked
      ? { seats_per_branch: seats }
      : {
          date: values.date,
          start_time: values.start_time,
          end_time: values.end_time ? values.end_time : null,
          seats_per_branch: seats,
          ...(slot ? {} : { course_id: values.course_id }),
        }

    const result = await run(body)
    if (result.ok) {
      onSaved(result.data)
      return
    }
    const error = result.error
    if (!error) return
    if (error.status === 422) {
      const fields = error.details?.fields ?? []
      setErrors(Object.fromEntries(fields.map((field) => [field.field, field.message])))
    }
    setAlert(error.message)
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={slot ? 'Edit exam slot' : 'Add exam slot'}
      description={
        timesLocked ? 'Students have chosen this slot, so only seats can change.' : undefined
      }
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button form="slot-form" type="submit" pending={pending} pendingLabel="Saving">
            {slot ? 'Save changes' : 'Add exam slot'}
          </Button>
        </>
      }
    >
      <form id="slot-form" noValidate onSubmit={onSubmit} className="mt-4 space-y-5">
        <Field id="slot-course" label="Course" error={errors.course_id}>
          {(props) => (
            <Select
              {...props}
              value={values.course_id}
              disabled={Boolean(slot)}
              onChange={setValue('course_id')}
              options={[
                { value: '', label: 'Choose a course' },
                ...courses.map((course) => ({
                  value: course.id,
                  label: `${course.code} ${course.title}`,
                })),
              ]}
            />
          )}
        </Field>

        <div className="grid gap-5 sm:grid-cols-2">
          <Field id="slot-date" label="Date" error={errors.date}>
            {(props) => (
              <TextInput
                {...props}
                type="date"
                value={values.date}
                disabled={timesLocked}
                onChange={setValue('date')}
              />
            )}
          </Field>
          <Field id="slot-seats" label="Seats per branch" error={errors.seats_per_branch}>
            {(props) => (
              <TextInput
                {...props}
                type="number"
                min={1}
                max={1000}
                value={values.seats_per_branch}
                onChange={setValue('seats_per_branch')}
              />
            )}
          </Field>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <Field id="slot-start" label="Start time" error={errors.start_time}>
            {(props) => (
              <TextInput
                {...props}
                type="time"
                value={values.start_time}
                disabled={timesLocked}
                onChange={setValue('start_time')}
              />
            )}
          </Field>
          <Field
            id="slot-end"
            label="End time"
            optional
            hint="Leave empty to use the default length of 3 hours for clash checks."
            error={errors.end_time}
          >
            {(props) => (
              <TextInput
                {...props}
                type="time"
                value={values.end_time}
                disabled={timesLocked}
                onChange={setValue('end_time')}
              />
            )}
          </Field>
        </div>

        <FormAlert message={alert} />
      </form>
    </Dialog>
  )
}
