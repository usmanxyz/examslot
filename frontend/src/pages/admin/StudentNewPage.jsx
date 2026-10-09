import { useNavigate } from 'react-router'

import PageHeader from '../../components/ui/PageHeader'
import StudentForm from '../../features/admin/StudentForm'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { createStudent } from '../../services/admin/studentService'

export default function StudentNewPage() {
  useDocumentTitle('New student')
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  return (
    <div className="mx-auto w-full max-w-[60rem] space-y-8">
      <PageHeader title="New student" meta="The student receives an email to set their password." />
      <StudentForm
        submitLabel="Create student"
        onSubmit={(body) => createStudent(api, body)}
        onCancel={() => navigate('/admin/students')}
        onDone={(student) => {
          showToast(
            student.latest_link?.delivery_status === 'failed'
              ? 'Student created, but the setup email could not be sent. Use Resend setup email.'
              : 'Student created. Setup email sent.',
          )
          navigate(`/admin/students/${student.id}`)
        }}
      />
    </div>
  )
}
