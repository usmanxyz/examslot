import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import Button from '../../components/ui/Button'
import Checkbox from '../../components/ui/Checkbox'
import ErrorState from '../../components/ui/ErrorState'
import PageHeader from '../../components/ui/PageHeader'
import SearchInput from '../../components/ui/SearchInput'
import Skeleton from '../../components/ui/Skeleton'
import FormAlert from '../../features/auth/FormAlert'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useMutation } from '../../hooks/useMutation'
import { useQuery } from '../../hooks/useQuery'
import {
  getStudentAssignments,
  saveStudentAssignments,
} from '../../services/admin/assignmentService'
import { listCourses } from '../../services/admin/courseService'
import { getStudent } from '../../services/admin/studentService'

const MIN_COURSES = 4
const MAX_COURSES = 6

export default function AssignmentEditorPage() {
  useDocumentTitle('Assign courses')
  const { studentId } = useParams()
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const [selected, setSelected] = useState(null)
  const [seeded, setSeeded] = useState(null)
  const [search, setSearch] = useState('')
  const [alert, setAlert] = useState(null)
  const [courses, setCourses] = useState([])

  const loadAssignments = useCallback((signal) => getStudentAssignments(api, studentId, signal), [api, studentId])
  const loadStudent = useCallback((signal) => getStudent(api, studentId, signal), [api, studentId])
  const assignments = useQuery(loadAssignments)
  const student = useQuery(loadStudent)
  const { run, pending } = useMutation((ids) => saveStudentAssignments(api, studentId, ids))

  useEffect(() => {
    const controller = new AbortController()
    listCourses(api, 'page=1&page_size=100&sort=code&order=asc', controller.signal)
      .then((result) => setCourses(result.items))
      .catch(() => setCourses([]))
    return () => controller.abort()
  }, [api])

  if (assignments.status === 'success' && seeded !== assignments.data) {
    setSeeded(assignments.data)
    setSelected(assignments.data.courses.map((course) => course.id))
  }

  if (assignments.status === 'loading' || student.status === 'loading' || selected === null) {
    return (
      <div aria-busy="true" className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-6 w-96" />
        <Skeleton className="h-80 w-full rounded-xl" />
      </div>
    )
  }

  if (assignments.status === 'error') {
    return <ErrorState message={assignments.error?.message} onRetry={assignments.reload} />
  }

  const editable = assignments.data.editable
  const assignedIds = new Set(assignments.data.courses.map((course) => course.id))
  const visible = courses.filter((course) => {
    if (course.status !== 'active' && !assignedIds.has(course.id)) return false
    if (!search.trim()) return true
    const text = `${course.code} ${course.title} ${course.department}`.toLowerCase()
    return text.includes(search.trim().toLowerCase())
  })
  const selectedCourses = courses.filter((course) => selected.includes(course.id))
  const countValid = selected.length >= MIN_COURSES && selected.length <= MAX_COURSES

  const toggle = (courseId) => {
    setSelected((current) =>
      current.includes(courseId) ? current.filter((id) => id !== courseId) : [...current, courseId],
    )
  }

  const onSave = async () => {
    setAlert(null)
    const result = await run(selected)
    if (result.ok) {
      showToast('Courses saved.')
      navigate('/admin/assignments')
      return
    }
    setAlert(result.error?.message)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Assign courses"
        meta={
          student.status === 'success'
            ? `${student.data.full_name} · ${student.data.registration_no} · ${student.data.program}`
            : undefined
        }
      >
        <Link to="/admin/assignments" className="inline-flex min-h-11 items-center text-base text-primary">
          Back to assignments
        </Link>
      </PageHeader>

      {!editable ? (
        <p className="rounded-lg bg-warning-soft px-3 py-2 text-[15px] leading-6 text-warning">
          This student has saved a date sheet. Courses can change only after you approve their date sheet change
          request.
        </p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <SearchInput
            id="course-search"
            label="Search courses"
            placeholder="Search code, title or department"
            value={search}
            onChange={setSearch}
          />
          <ul className="divide-y divide-line rounded-xl border border-line bg-surface">
            {visible.map((course) => (
              <li key={course.id} className="flex items-center gap-3 p-4">
                <Checkbox
                  id={`course-${course.id}`}
                  checked={selected.includes(course.id)}
                  disabled={!editable}
                  onChange={() => toggle(course.id)}
                  label={
                    <span className="block">
                      <span className="tabular font-medium text-ink">{course.code}</span>{' '}
                      <span className="text-ink">{course.title}</span>
                      <span className="block text-sm text-muted">
                        {course.credit_hours} credit hours · {course.department}
                      </span>
                    </span>
                  }
                />
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <section className="rounded-xl border border-line bg-surface p-5">
            <h2 className="font-serif text-[22px] leading-7 font-semibold tracking-[-0.01em]">Selected</h2>
            <p className="tabular mt-2 text-[15px] text-muted">
              {selected.length} selected. Assign between {MIN_COURSES} and {MAX_COURSES}.
            </p>
            <ul className="mt-4 space-y-2">
              {selectedCourses.map((course) => (
                <li key={course.id} className="flex items-center justify-between gap-3">
                  <span className="text-[15px] leading-6 text-ink">
                    <span className="tabular font-medium">{course.code}</span> {course.title}
                  </span>
                  {editable ? (
                    <Button variant="tertiary" size="sm" onClick={() => toggle(course.id)}>
                      Remove
                    </Button>
                  ) : null}
                </li>
              ))}
            </ul>
            <div className="mt-5 space-y-3">
              <FormAlert message={alert} />
              <Button
                className="w-full"
                disabled={!editable || !countValid}
                pending={pending}
                pendingLabel="Saving"
                onClick={onSave}
              >
                Save courses
              </Button>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
