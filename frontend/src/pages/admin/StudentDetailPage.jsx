import { useCallback, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import Button from '../../components/ui/Button'
import DefinitionList from '../../components/ui/DefinitionList'
import EmptyState from '../../components/ui/EmptyState'
import ErrorState from '../../components/ui/ErrorState'
import OverflowMenu from '../../components/ui/OverflowMenu'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import StatusPill from '../../components/ui/StatusPill'
import Tabs, { TabPanel } from '../../components/ui/Tabs'
import StudentPhoto from '../../features/admin/StudentPhoto'
import DateSheetTable from '../../features/student/DateSheetTable'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useQuery } from '../../hooks/useQuery'
import {
  deactivateStudent,
  getStudent,
  getStudentDateSheet,
  getStudentRequests,
  reactivateStudent,
  sendSetupEmail,
} from '../../services/admin/studentService'
import { getStudentAssignments } from '../../services/admin/assignmentService'
import {
  formatCnic,
  formatDate,
  formatDateTime,
  formatPhone,
  formatScore,
  titleCase,
} from '../../lib/format'

const TABS = [
  { value: 'record', label: 'Record' },
  { value: 'courses', label: 'Courses' },
  { value: 'date-sheet', label: 'Date sheet' },
  { value: 'requests', label: 'Requests' },
]

const TYPE_LABELS = {
  branch_change: 'Branch change',
  date_sheet_change: 'Date sheet change',
}

function RecordTab({ student, onPhotoChange }) {
  const personal = [
    { term: 'Full name', value: student.full_name },
    { term: 'Email', value: student.email },
    { term: 'Mobile number', value: formatPhone(student.phone) },
    { term: 'CNIC or B-Form', value: formatCnic(student.cnic) },
    { term: 'Date of birth', value: formatDate(student.date_of_birth) },
    { term: 'Gender', value: titleCase(student.gender) },
    { term: 'Address', value: student.address },
  ]
  const guardian = [
    { term: 'Guardian name', value: student.guardian_name },
    { term: 'Guardian CNIC', value: formatCnic(student.guardian_cnic) },
    { term: 'Occupation', value: student.guardian_occupation },
    { term: 'Guardian mobile', value: formatPhone(student.guardian_phone) },
    { term: 'Emergency contact', value: formatPhone(student.emergency_phone) },
  ]
  const academic = [
    { term: 'Registration number', value: student.registration_no },
    { term: 'Program', value: student.program },
    { term: 'Semester', value: String(student.semester) },
    { term: 'Session', value: student.session },
    { term: 'Previous qualification', value: student.previous_qualification },
    { term: 'Previous institute', value: student.previous_institute },
    { term: 'Previous score', value: formatScore(student.previous_score_type, student.previous_score) },
    { term: 'Branch', value: student.branch ? `${student.branch.code} ${student.branch.name}` : 'Not chosen' },
    { term: 'Last sign-in', value: student.last_login_at ? formatDateTime(student.last_login_at) : 'Never' },
  ]

  return (
    <div className="grid gap-8 lg:grid-cols-[10rem_1fr]">
      <StudentPhoto studentId={student.id} hasPhoto={student.has_photo} onChange={onPhotoChange} />
      <div className="space-y-8">
        <section className="space-y-4">
          <h2 className="text-[17px] leading-6 font-semibold text-ink">Personal</h2>
          <DefinitionList items={personal} columns={2} />
        </section>
        <section className="space-y-4">
          <h2 className="text-[17px] leading-6 font-semibold text-ink">Guardian</h2>
          <DefinitionList items={guardian} columns={2} />
        </section>
        <section className="space-y-4">
          <h2 className="text-[17px] leading-6 font-semibold text-ink">Academic</h2>
          <DefinitionList items={academic} columns={2} />
        </section>
      </div>
    </div>
  )
}

function CoursesTab({ studentId }) {
  const { api } = useAdminAuth()
  const load = useCallback((signal) => getStudentAssignments(api, studentId, signal), [api, studentId])
  const { status, data, error, reload } = useQuery(load)

  if (status === 'loading') return <Skeleton className="h-40 w-full rounded-xl" />
  if (status === 'error') return <ErrorState message={error?.message} onRetry={reload} />
  if (data.courses.length === 0) {
    return (
      <EmptyState title="No courses assigned" body="Assign 4 to 6 courses so this student can plan.">
        <Link to={`/admin/assignments/${studentId}`} className="text-base text-primary">
          Assign courses
        </Link>
      </EmptyState>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <StatusPill status={data.status} />
        <Link to={`/admin/assignments/${studentId}`} className="text-base text-primary">
          Edit courses
        </Link>
      </div>
      <ul className="divide-y divide-line rounded-xl border border-line bg-surface">
        {data.courses.map((course) => (
          <li key={course.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
            <span className="text-[15px] leading-6 text-ink">
              <span className="tabular font-medium">{course.code}</span> {course.title}
            </span>
            <span className="tabular text-sm text-muted">{course.credit_hours} credit hours</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function DateSheetTab({ studentId }) {
  const { api } = useAdminAuth()
  const load = useCallback((signal) => getStudentDateSheet(api, studentId, signal), [api, studentId])
  const { status, data, error, reload } = useQuery(load)

  if (status === 'loading') return <Skeleton className="h-40 w-full rounded-xl" />
  if (status === 'error') {
    if (error?.code === 'DATE_SHEET_NOT_SAVED') {
      return <EmptyState title="No date sheet yet" body="This student has not saved their exam times." />
    }
    return <ErrorState message={error?.message} onRetry={reload} />
  }

  return (
    <div className="space-y-4">
      <DateSheetTable entries={data.entries} />
      <p className="text-sm text-muted">Saved on {formatDateTime(data.saved_at)}. All times are Pakistan time.</p>
    </div>
  )
}

function RequestsTab({ studentId }) {
  const { api } = useAdminAuth()
  const load = useCallback((signal) => getStudentRequests(api, studentId, signal), [api, studentId])
  const { status, data, error, reload } = useQuery(load)

  if (status === 'loading') return <Skeleton className="h-40 w-full rounded-xl" />
  if (status === 'error') return <ErrorState message={error?.message} onRetry={reload} />
  if (data.items.length === 0) {
    return <EmptyState title="No requests" body="This student has not asked for a change." />
  }

  return (
    <ul className="space-y-3">
      {data.items.map((request) => (
        <li key={request.id} className="rounded-xl border border-line bg-surface p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-[17px] leading-6 font-semibold text-ink">{TYPE_LABELS[request.type]}</p>
            <StatusPill status={request.status} />
          </div>
          <p className="mt-2 text-base text-muted">{request.reason}</p>
          <p className="tabular mt-3 text-sm text-muted">Sent {formatDateTime(request.created_at)}</p>
          {request.admin_remark ? (
            <p className="mt-1 text-sm text-muted">Exam office: {request.admin_remark}</p>
          ) : null}
        </li>
      ))}
    </ul>
  )
}

export default function StudentDetailPage() {
  const { studentId } = useParams()
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const [tab, setTab] = useState('record')

  const load = useCallback((signal) => getStudent(api, studentId, signal), [api, studentId])
  const { status, data, error, reload } = useQuery(load)
  useDocumentTitle(status === 'success' ? data.full_name : 'Student')

  if (status === 'loading') {
    return (
      <div aria-busy="true" className="space-y-6">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-6 w-96" />
        <Skeleton className="h-80 w-full rounded-xl" />
      </div>
    )
  }

  if (status === 'error') {
    return (
      <ErrorState
        variant={error?.status === 404 ? 'notFound' : 'server'}
        message={error?.message}
        onRetry={reload}
      >
        <Link to="/admin/students" className="text-base text-primary">
          Back to students
        </Link>
      </ErrorState>
    )
  }

  const link = data.latest_link

  return (
    <div className="space-y-6">
      <PageHeader title={data.full_name} meta={`${data.registration_no} · ${data.program}`}>
        <Button variant="secondary" onClick={() => navigate(`/admin/students/${studentId}/edit`)}>
          Edit
        </Button>
        <Button variant="secondary" onClick={() => navigate(`/admin/assignments/${studentId}`)}>
          Assign courses
        </Button>
        <OverflowMenu
          label={`More actions for ${data.full_name}`}
          items={[
            {
              label: 'Resend setup email',
              disabled: data.account_status !== 'invited',
              disabledReason: 'This student already set a password.',
              onSelect: async () => {
                await sendSetupEmail(api, studentId)
                showToast('Setup email sent.')
                reload()
              },
            },
            {
              label: data.account_status === 'inactive' ? 'Reactivate' : 'Deactivate',
              onSelect: async () => {
                if (data.account_status === 'inactive') {
                  await reactivateStudent(api, studentId)
                  showToast('Student reactivated.')
                } else {
                  await deactivateStudent(api, studentId)
                  showToast('Student deactivated.')
                }
                reload()
              },
            },
          ]}
        />
      </PageHeader>

      <div className="flex flex-wrap items-center gap-3">
        <StatusPill status={data.account_status} />
        <StatusPill status={data.progress} />
      </div>

      {data.account_status === 'invited' ? (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-warning-soft px-4 py-3">
          <p className="text-[15px] leading-6 text-warning">
            {link && link.delivery_status === 'sent'
              ? `Setup email sent on ${formatDateTime(link.created_at)}. The link works until ${formatDateTime(link.expires_at)}.`
              : 'The setup email was not sent.'}
          </p>
          <Button
            variant="secondary"
            size="sm"
            onClick={async () => {
              await sendSetupEmail(api, studentId)
              showToast('Setup email sent.')
              reload()
            }}
          >
            Resend setup email
          </Button>
        </div>
      ) : null}

      <Tabs tabs={TABS} value={tab} onChange={setTab} />

      <TabPanel>
        {tab === 'record' ? <RecordTab student={data} onPhotoChange={reload} /> : null}
        {tab === 'courses' ? <CoursesTab studentId={studentId} /> : null}
        {tab === 'date-sheet' ? <DateSheetTab studentId={studentId} /> : null}
        {tab === 'requests' ? <RequestsTab studentId={studentId} /> : null}
      </TabPanel>
    </div>
  )
}
