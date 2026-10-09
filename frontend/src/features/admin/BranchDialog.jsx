import { useState } from 'react'

import Button from '../../components/ui/Button'
import Dialog from '../../components/ui/Dialog'
import Field from '../../components/ui/Field'
import Select from '../../components/ui/Select'
import TextInput from '../../components/ui/TextInput'
import FormAlert from '../auth/FormAlert'
import { useMutation } from '../../hooks/useMutation'
import { validateLength, validatePhone } from '../../lib/validators'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

function emptyBranch() {
  return { code: '', name: '', city: '', address: '', contact_phone: '', status: 'active' }
}

export default function BranchDialog({ open, branch, onClose, onSave, onSaved }) {
  const [values, setValues] = useState(() => (branch ? { ...branch } : emptyBranch()))
  const [errors, setErrors] = useState({})
  const [alert, setAlert] = useState(null)
  const { run, pending } = useMutation(onSave)

  const setValue = (key) => (event) => setValues((current) => ({ ...current, [key]: event.target.value }))

  const onSubmit = async (event) => {
    event.preventDefault()
    setAlert(null)
    const next = {
      code: validateLength(values.code, 'Code', 2, 10),
      name: validateLength(values.name, 'Name', 2, 120),
      city: validateLength(values.city, 'City', 2, 80),
      address: validateLength(values.address, 'Address', 5, 255),
      contact_phone: validatePhone(values.contact_phone),
    }
    setErrors(next)
    if (Object.values(next).some(Boolean)) return

    const result = await run({
      code: values.code.trim().toUpperCase(),
      name: values.name.trim(),
      city: values.city.trim(),
      address: values.address.trim(),
      contact_phone: values.contact_phone.trim(),
      status: values.status,
    })
    if (result.ok) {
      onSaved(result.data)
      return
    }
    const error = result.error
    if (!error) return
    if (error.code === 'BRANCH_CODE_TAKEN') {
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
      title={branch ? 'Edit branch' : 'Add branch'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button form="branch-form" type="submit" pending={pending} pendingLabel="Saving">
            {branch ? 'Save changes' : 'Add branch'}
          </Button>
        </>
      }
    >
      <form id="branch-form" noValidate onSubmit={onSubmit} className="space-y-5">
        <div className="grid gap-5 sm:grid-cols-2">
          <Field id="branch-code" label="Code" error={errors.code}>
            {(props) => <TextInput {...props} value={values.code} onChange={setValue('code')} />}
          </Field>
          <Field id="branch-city" label="City" error={errors.city}>
            {(props) => <TextInput {...props} value={values.city} onChange={setValue('city')} />}
          </Field>
        </div>
        <Field id="branch-name" label="Name" error={errors.name}>
          {(props) => <TextInput {...props} value={values.name} onChange={setValue('name')} />}
        </Field>
        <Field id="branch-address" label="Address" error={errors.address}>
          {(props) => <TextInput {...props} value={values.address} onChange={setValue('address')} />}
        </Field>
        <div className="grid gap-5 sm:grid-cols-2">
          <Field id="branch-phone" label="Contact number" error={errors.contact_phone}>
            {(props) => (
              <TextInput {...props} value={values.contact_phone} onChange={setValue('contact_phone')} />
            )}
          </Field>
          <Field id="branch-status" label="Status" error={errors.status}>
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
