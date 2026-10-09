import { useCallback } from 'react'
import { useNavigate, useParams } from 'react-router'

import ErrorState from '../../components/ui/ErrorState'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import StudentForm from '../../features/admin/StudentForm'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useQuery } from '../../hooks/useQuery'
import { getStudent, updateStudent } from '../../services/admin/studentService'

export default function StudentEditPage() {
  useDocumentTitle('Edit student')
  const { studentId } = useParams()
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const load = useCallback((signal) => getStudent(api, studentId, signal), [api, studentId])
  const { status, data, error, reload } = useQuery(load)

  if (status === 'loading') {
    return (
      <div aria-busy="true" className="mx-auto w-full max-w-[60rem] space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full rounded-xl" />
      </div>
    )
  }

  if (status === 'error') {
    return (
      <ErrorState
        variant={error?.status === 404 ? 'notFound' : 'server'}
        message={error?.message}
        onRetry={reload}
      />
    )
  }

  return (
    <div className="mx-auto w-full max-w-[60rem] space-y-8">
      <PageHeader title="Edit student" meta={`${data.full_name} · ${data.registration_no}`} />
      <StudentForm
        student={data}
        submitLabel="Save changes"
        onSubmit={(body) => updateStudent(api, studentId, body)}
        onCancel={() => navigate(`/admin/students/${studentId}`)}
        onDone={() => {
          showToast('Changes saved.')
          navigate(`/admin/students/${studentId}`)
        }}
      />
    </div>
  )
}
