import { useState } from 'react'

import Button from '../../components/ui/Button'
import Dialog from '../../components/ui/Dialog'
import Field from '../../components/ui/Field'
import Select from '../../components/ui/Select'
import TextInput from '../../components/ui/TextInput'
import FormAlert from '../auth/FormAlert'
import { useMutation } from '../../hooks/useMutation'
import { validateLength, validateRange } from '../../lib/validators'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

function emptyCourse() {
  return { code: '', title: '', credit_hours: '3', department: '', status: 'active' }
}

export default function CourseDialog({ open, course, onClose, onSave, onSaved }) {
  const [values, setValues] = useState(() =>
    course ? { ...course, credit_hours: String(course.credit_hours) } : emptyCourse(),
  )
  const [errors, setErrors] = useState({})
  const [alert, setAlert] = useState(null)
  const { run, pending } = useMutation(onSave)

  const setValue = (key) => (event) => setValues((current) => ({ ...current, [key]: event.target.value }))

  const onSubmit = async (event) => {
    event.preventDefault()
    setAlert(null)
    const next = {
      code: validateLength(values.code, 'Code', 2, 20),
      title: validateLength(values.title, 'Title', 2, 120),
      department: validateLength(values.department, 'Department', 2, 100),
      credit_hours: validateRange(values.credit_hours, 'Credit hours', 1, 6),
    }
    setErrors(next)
    if (Object.values(next).some(Boolean)) return

    const result = await run({
      code: values.code.trim().toUpperCase(),
      title: values.title.trim(),
      credit_hours: Number(values.credit_hours),
      department: values.department.trim(),
      status: values.status,
    })
    if (result.ok) {
      onSaved(result.data)
      return
    }
    const error = result.error
    if (!error) return
    if (error.code === 'COURSE_CODE_TAKEN') {
      setErrors({ code: error.message })
      return
    }
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
      title={course ? 'Edit course' : 'Add course'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button form="course-form" type="submit" pending={pending} pendingLabel="Saving">
            {course ? 'Save changes' : 'Add course'}
          </Button>
        </>
      }
    >
      <form id="course-form" noValidate onSubmit={onSubmit} className="space-y-5">
        <div className="grid gap-5 sm:grid-cols-2">
          <Field id="course-code" label="Code" error={errors.code}>
            {(props) => <TextInput {...props} value={values.code} onChange={setValue('code')} />}
          </Field>
          <Field id="course-credits" label="Credit hours" error={errors.credit_hours}>
            {(props) => (
              <TextInput
                {...props}
                type="number"
                min={1}
                max={6}
                value={values.credit_hours}
                onChange={setValue('credit_hours')}
              />
            )}
          </Field>
        </div>
        <Field id="course-title" label="Title" error={errors.title}>
          {(props) => <TextInput {...props} value={values.title} onChange={setValue('title')} />}
        </Field>
        <div className="grid gap-5 sm:grid-cols-2">
          <Field id="course-department" label="Department" error={errors.department}>
            {(props) => <TextInput {...props} value={values.department} onChange={setValue('department')} />}
          </Field>
          <Field id="course-status" label="Status" error={errors.status}>
            {(props) => (
              <Select {...props} value={values.status} onChange={setValue('status')} options={STATUS_OPTIONS} />
            )}
          </Field>
        </div>
        <FormAlert message={alert} />
      </form>
    </Dialog>
  )
}
