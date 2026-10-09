import { useEffect, useRef, useState } from 'react'
import { UserRound } from 'lucide-react'

import Button from '../../components/ui/Button'
import FormAlert from '../auth/FormAlert'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { deleteStudentPhoto, uploadStudentPhoto } from '../../services/admin/studentService'

const TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_BYTES = 2 * 1024 * 1024

export default function StudentPhoto({ studentId, hasPhoto, onChange }) {
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const [source, setSource] = useState(null)
  const [alert, setAlert] = useState(null)
  const [pending, setPending] = useState(false)
  const fileInput = useRef(null)

  useEffect(() => {
    if (!hasPhoto) return undefined
    let url = null
    let live = true
    api
      .getBlob(`/admin/students/${studentId}/photo`)
      .then((blob) => {
        if (!live) return
        url = URL.createObjectURL(blob)
        setSource(url)
      })
      .catch(() => setSource(null))
    return () => {
      live = false
      if (url) URL.revokeObjectURL(url)
    }
  }, [api, studentId, hasPhoto])

  const onPick = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setAlert(null)
    if (!TYPES.includes(file.type)) {
      setAlert('Use a JPEG, PNG or WebP image.')
      return
    }
    if (file.size > MAX_BYTES) {
      setAlert('Use an image of 2 MB or less.')
      return
    }
    setPending(true)
    try {
      const bytes = await file.arrayBuffer()
      await uploadStudentPhoto(api, studentId, bytes, file.type)
      showToast('Photo updated.')
      onChange(true)
    } catch (error) {
      setAlert(error.message)
    } finally {
      setPending(false)
    }
  }

  const onRemove = async () => {
    setAlert(null)
    setPending(true)
    try {
      await deleteStudentPhoto(api, studentId)
      showToast('Photo removed.')
      onChange(false)
    } catch (error) {
      setAlert(error.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex size-[10rem] items-center justify-center overflow-hidden rounded-xl border border-line bg-sunken">
        {hasPhoto && source ? (
          <img src={source} alt="Student photo" className="size-full object-cover" />
        ) : (
          <UserRound size={48} strokeWidth={1.25} aria-hidden="true" className="text-muted" />
        )}
      </div>
      <input
        ref={fileInput}
        type="file"
        accept={TYPES.join(',')}
        className="sr-only"
        onChange={onPick}
      />
      <div className="flex flex-wrap gap-3">
        <Button variant="secondary" size="sm" pending={pending} onClick={() => fileInput.current?.click()}>
          {hasPhoto ? 'Replace photo' : 'Upload photo'}
        </Button>
        {hasPhoto ? (
          <Button variant="tertiary" size="sm" disabled={pending} onClick={onRemove}>
            Remove
          </Button>
        ) : null}
      </div>
      <FormAlert message={alert} />
    </div>
  )
}
