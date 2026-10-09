import { useRef, useState } from 'react'

import Button from '../../components/ui/Button'
import Field from '../../components/ui/Field'
import Select from '../../components/ui/Select'
import TextInput from '../../components/ui/TextInput'
import FormAlert from '../auth/FormAlert'
import { useMutation } from '../../hooks/useMutation'
import {
  digitsOnly,
  validateCnic,
  validateEmail,
  validateLength,
  validateMobile,
  validatePhone,
  validateRange,
} from '../../lib/validators'

const GENDERS = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
  { value: 'transgender', label: 'Transgender' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
]

const SCORE_TYPES = [
  { value: 'percentage', label: 'Percentage' },
  { value: 'cgpa', label: 'CGPA' },
]

const LABELS = {
  full_name: 'Full name',
  email: 'Email',
  phone: 'Mobile number',
  cnic: 'CNIC or B-Form number',
  date_of_birth: 'Date of birth',
  gender: 'Gender',
  address: 'Address',
  guardian_name: 'Guardian name',
  guardian_cnic: 'Guardian CNIC',
  guardian_occupation: 'Guardian occupation',
  guardian_phone: 'Guardian mobile number',
  emergency_phone: 'Emergency contact number',
  registration_no: 'Registration number',
  program: 'Program',
  semester: 'Semester',
  session: 'Session',
  previous_qualification: 'Previous qualification',
  previous_institute: 'Previous institute',
  previous_score_type: 'Score type',
  previous_score: 'Score',
}

const EMPTY = {
  full_name: '',
  email: '',
  phone: '',
  cnic: '',
  date_of_birth: '',
  gender: 'prefer_not_to_say',
  address: '',
  guardian_name: '',
  guardian_cnic: '',
  guardian_occupation: '',
  guardian_phone: '',
  emergency_phone: '',
  registration_no: '',
  program: '',
  semester: '1',
  session: '',
  previous_qualification: '',
  previous_institute: '',
  previous_score_type: 'percentage',
  previous_score: '',
}

function fromStudent(student) {
  return Object.fromEntries(
    Object.keys(EMPTY).map((key) => [
      key,
      student[key] === null || student[key] === undefined ? '' : String(student[key]),
    ]),
  )
}

function validate(values) {
  const scoreMax = values.previous_score_type === 'cgpa' ? 4 : 100
  return {
    full_name: validateLength(values.full_name, LABELS.full_name, 2, 120),
    email: validateEmail(values.email),
    phone: validateMobile(values.phone),
    cnic: validateCnic(values.cnic),
    date_of_birth: values.date_of_birth ? null : 'Date of birth is required.',
    address: validateLength(values.address, LABELS.address, 5, 255),
    guardian_name: validateLength(values.guardian_name, LABELS.guardian_name, 2, 120),
    guardian_cnic: validateCnic(values.guardian_cnic),
    guardian_occupation: validateLength(values.guardian_occupation, LABELS.guardian_occupation, 2, 100),
    guardian_phone: validateMobile(values.guardian_phone),
    emergency_phone: validatePhone(values.emergency_phone),
    registration_no: validateLength(values.registration_no, LABELS.registration_no, 4, 30),
    program: validateLength(values.program, LABELS.program, 2, 120),
    semester: validateRange(values.semester, LABELS.semester, 1, 12),
    session: validateLength(values.session, LABELS.session, 4, 30),
    previous_qualification: validateLength(values.previous_qualification, LABELS.previous_qualification, 2, 120),
    previous_institute: validateLength(values.previous_institute, LABELS.previous_institute, 2, 150),
    previous_score: validateRange(values.previous_score, LABELS.previous_score, 0, scoreMax),
  }
}

function toBody(values) {
  return {
    full_name: values.full_name.trim(),
    email: values.email.trim(),
    phone: values.phone.replace(/[\s-]/g, ''),
    cnic: digitsOnly(values.cnic),
    date_of_birth: values.date_of_birth,
    gender: values.gender,
    address: values.address.trim(),
    guardian_name: values.guardian_name.trim(),
    guardian_cnic: digitsOnly(values.guardian_cnic),
    guardian_occupation: values.guardian_occupation.trim(),
    guardian_phone: values.guardian_phone.replace(/[\s-]/g, ''),
    emergency_phone: values.emergency_phone.replace(/[\s-]/g, ''),
    registration_no: values.registration_no.trim().toUpperCase(),
    program: values.program.trim(),
    semester: Number(values.semester),
    session: values.session.trim(),
    previous_qualification: values.previous_qualification.trim(),
    previous_institute: values.previous_institute.trim(),
    previous_score_type: values.previous_score_type,
    previous_score: values.previous_score,
  }
}

function Fieldset({ legend, children }) {
  return (
    <fieldset className="space-y-5">
      <legend className="font-serif text-[22px] leading-7 font-semibold tracking-[-0.01em]">{legend}</legend>
      <div className="grid gap-5 sm:grid-cols-2">{children}</div>
    </fieldset>
  )
}

export default function StudentForm({ student, submitLabel, onSubmit, onDone, onCancel }) {
  const [values, setValues] = useState(() => (student ? fromStudent(student) : EMPTY))
  const [errors, setErrors] = useState({})
  const [alert, setAlert] = useState(null)
  const [summary, setSummary] = useState([])
  const summaryRef = useRef(null)
  const { run, pending } = useMutation(onSubmit)

  const setValue = (key) => (event) => setValues((current) => ({ ...current, [key]: event.target.value }))

  const text = (key, extra = {}) => (
    <Field key={key} id={`student-${key}`} label={LABELS[key]} error={errors[key]}>
      {(props) => <TextInput {...props} value={values[key]} onChange={setValue(key)} {...extra} />}
    </Field>
  )

  const choice = (key, options) => (
    <Field key={key} id={`student-${key}`} label={LABELS[key]} error={errors[key]}>
      {(props) => <Select {...props} value={values[key]} onChange={setValue(key)} options={options} />}
    </Field>
  )

  const submit = async (event) => {
    event.preventDefault()
    setAlert(null)
    const next = validate(values)
    setErrors(next)
    const failed = Object.keys(next).filter((key) => next[key])
    setSummary(failed)
    if (failed.length > 0) {
      summaryRef.current?.focus()
      return
    }

    const result = await run(toBody(values))
    if (result.ok) {
      onDone(result.data)
      return
    }
    const error = result.error
    if (!error) return
    if (error.status === 422 || error.status === 409) {
      const fields = error.details?.fields ?? []
      const mapped = Object.fromEntries(fields.map((field) => [field.field, field.message]))
      if (Object.keys(mapped).length > 0) {
        setErrors(mapped)
        setSummary(Object.keys(mapped))
        summaryRef.current?.focus()
      }
    }
    setAlert(error.message)
  }

  return (
    <form noValidate onSubmit={submit} className="space-y-10">
      {summary.length > 0 ? (
        <div
          ref={summaryRef}
          tabIndex={-1}
          role="alert"
          className="rounded-lg bg-danger-soft px-4 py-3 text-sm text-danger"
        >
          <p className="font-medium">Some fields need attention.</p>
          <ul className="mt-2 list-disc space-y-1 ps-5">
            {summary.map((key) => (
              <li key={key}>
                <a href={`#student-${key}`} className="underline">
                  {LABELS[key] ?? key}
                </a>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <Fieldset legend="Personal">
        {text('full_name')}
        {text('email', { type: 'email' })}
        {text('phone')}
        {text('cnic')}
        {text('date_of_birth', { type: 'date' })}
        {choice('gender', GENDERS)}
        <div className="sm:col-span-2">{text('address')}</div>
      </Fieldset>

      <Fieldset legend="Guardian">
        {text('guardian_name')}
        {text('guardian_cnic')}
        {text('guardian_occupation')}
        {text('guardian_phone')}
        {text('emergency_phone')}
      </Fieldset>

      <Fieldset legend="Academic">
        {text('registration_no')}
        {text('program')}
        {text('semester', { type: 'number', min: 1, max: 12 })}
        {text('session')}
        {text('previous_qualification')}
        {text('previous_institute')}
        {choice('previous_score_type', SCORE_TYPES)}
        {text('previous_score', { type: 'number', step: '0.01' })}
      </Fieldset>

      <FormAlert message={alert} />

      <div className="sticky bottom-0 flex flex-wrap justify-end gap-3 border-t border-line bg-canvas py-4">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" pending={pending} pendingLabel="Saving">
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}
