import { useCallback, useState } from 'react'

import Button from '../../components/ui/Button'
import EmptyState from '../../components/ui/EmptyState'
import ErrorState from '../../components/ui/ErrorState'
import Field from '../../components/ui/Field'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import StatusPill from '../../components/ui/StatusPill'
import TextInput from '../../components/ui/TextInput'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useQuery } from '../../hooks/useQuery'
import { listStudents } from '../../services/admin/studentService'

const PAGE_SIZE = 20

export default function AdminStudentsPage() {
  useDocumentTitle('Students')
  const { api } = useAdminAuth()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const debounced = useDebouncedValue(search, 300)

  const load = useCallback(
    (signal) => listStudents(api, { page, page_size: PAGE_SIZE, q: debounced.trim() }, signal),
    [api, page, debounced],
  )
  const students = useQuery(load)

  const onSearch = (value) => {
    setSearch(value)
    setPage(1)
  }

  const data = students.data
  const total = data?.total ?? 0
  const from = total === 0 ? 0 : (data.page - 1) * data.page_size + 1
  const to = data ? Math.min(data.page * data.page_size, total) : 0

  return (
    <div className="space-y-6">
      <PageHeader title="Students" meta="Search the student records the exam office has created." />

      <Field id="student-search" label="Search by name, email or registration number">
        {(props) => (
          <TextInput
            {...props}
            type="search"
            className="max-w-[26rem]"
            value={search}
            onChange={(event) => onSearch(event.target.value)}
          />
        )}
      </Field>

      {students.status === 'loading' ? (
        <div aria-busy="true" className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : null}

      {students.status === 'error' ? (
        <ErrorState
          variant={students.error?.code === 'NETWORK_ERROR' ? 'network' : 'server'}
          message={students.error?.message}
          onRetry={students.reload}
        />
      ) : null}

      {students.status === 'success' && data.items.length === 0 ? (
        <EmptyState
          title={debounced.trim() ? 'No results for that search.' : 'No students yet.'}
          body={
            debounced.trim()
              ? 'Check the spelling or clear the search.'
              : 'Create a student to send their setup email.'
          }
        />
      ) : null}

      {students.status === 'success' && data.items.length > 0 ? (
        <>
          <div className="overflow-hidden rounded-xl border border-line bg-surface">
            <table className="w-full border-collapse text-left text-sm">
              <caption className="sr-only">Students</caption>
              <thead>
                <tr className="bg-sunken">
                  <th scope="col" className="px-4 py-3 font-medium text-muted">
                    Name
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium text-muted">
                    Registration no.
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium text-muted">
                    Program and semester
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium text-muted">
                    Branch
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium text-muted">
                    Progress
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium text-muted">
                    Account
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((student) => (
                  <tr key={student.id} className="border-t border-line">
                    <td className="px-4 py-3 font-medium text-ink">{student.full_name}</td>
                    <td className="tabular px-4 py-3 text-ink">{student.registration_no}</td>
                    <td className="tabular px-4 py-3 text-ink">
                      {`${student.program}, semester ${student.semester}`}
                    </td>
                    <td className="px-4 py-3 text-ink">{student.branch?.name ?? 'Not chosen yet'}</td>
                    <td className="px-4 py-3">
                      <StatusPill status={student.progress} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusPill status={student.account_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="tabular text-sm text-muted">{`Showing ${from} to ${to} of ${total}`}</p>
            <div className="flex items-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                disabled={data.page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={data.page >= data.total_pages}
                onClick={() => setPage((current) => current + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}
