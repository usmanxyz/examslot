import { useCallback } from 'react'
import { Link } from 'react-router'

import Button from '../../components/ui/Button'
import DataTable from '../../components/ui/DataTable'
import EmptyState from '../../components/ui/EmptyState'
import ErrorState from '../../components/ui/ErrorState'
import PageHeader from '../../components/ui/PageHeader'
import Pagination from '../../components/ui/Pagination'
import StatusPill from '../../components/ui/StatusPill'
import ListToolbar from '../../features/admin/ListToolbar'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useListParams } from '../../hooks/useListParams'
import { useQuery } from '../../hooks/useQuery'
import { listAssignments } from '../../services/admin/assignmentService'

const STATUS_FILTER = [
  { value: 'incomplete', label: 'Incomplete' },
  { value: 'complete', label: 'Complete' },
  { value: 'locked', label: 'Locked' },
]

export default function AssignmentsPage() {
  useDocumentTitle('Assignments')
  const { api } = useAdminAuth()
  const params = useListParams({ sort: 'full_name', order: 'asc', filters: ['status'] })

  const query = params.queryString
  const load = useCallback((signal) => listAssignments(api, query, signal), [api, query])
  const { status, data, error, reload } = useQuery(load)

  const rows = data?.items ?? []
  const searching = Boolean(params.q || params.activeFilterCount)

  const columns = [
    {
      key: 'student',
      header: 'Student',
      sort: 'full_name',
      primary: true,
      cell: (row) => (
        <Link to={`/admin/students/${row.student.id}`} className="text-primary">
          {row.student.full_name} <span className="tabular">{row.student.registration_no}</span>
        </Link>
      ),
    },
    {
      key: 'courses',
      header: 'Courses',
      cell: (row) => (
        <span className="flex flex-wrap gap-1.5">
          {row.courses.map((course) => (
            <span key={course.id} className="tabular rounded-full bg-sunken px-2 py-0.5 text-sm text-ink">
              {course.code}
            </span>
          ))}
        </span>
      ),
    },
    { key: 'count', header: 'Count', sort: 'course_count', cell: (row) => <span className="tabular">{row.course_count}</span> },
    { key: 'status', header: 'Status', cell: (row) => <StatusPill status={row.status} /> },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Assignments" meta="Each student needs 4 to 6 courses before they can plan." />

      <ListToolbar
        search={{
          label: 'Search assignments',
          placeholder: 'Search student, registration number or course code',
          value: params.q,
          onChange: (value) => params.update({ q: value }),
        }}
        filters={[
          {
            id: 'filter-status',
            label: 'Status',
            allLabel: 'All statuses',
            value: params.filters.status,
            onChange: (value) => params.update({ status: value }),
            options: STATUS_FILTER,
          },
        ]}
        activeFilterCount={params.activeFilterCount}
        onClear={params.clearFilters}
      />

      {status === 'error' ? <ErrorState message={error?.message} onRetry={reload} /> : null}

      {status !== 'error' ? (
        <DataTable
          caption="Course assignments"
          columns={columns}
          rows={rows}
          rowKey={(row) => row.student.id}
          cardTitle={(row) => row.student.full_name}
          loading={status === 'loading'}
          sort={params.sort}
          order={params.order}
          onSort={params.toggleSort}
          empty={
            searching ? (
              <EmptyState title="No results for that search" body="Check the spelling or clear the filters.">
                <Button variant="secondary" onClick={params.clearFilters}>
                  Clear filters
                </Button>
              </EmptyState>
            ) : (
              <EmptyState title="No students to assign yet" body="Create a student to assign their courses." />
            )
          }
          actions={(row) => (
            <Link
              to={`/admin/assignments/${row.student.id}`}
              className="inline-flex min-h-11 items-center text-base text-primary"
            >
              Edit
            </Link>
          )}
        />
      ) : null}

      {status === 'success' && rows.length > 0 ? (
        <Pagination
          page={params.page}
          pageSize={params.pageSize}
          pageSizes={params.pageSizes}
          total={data.total}
          totalPages={data.total_pages}
          onPageChange={(page) => params.update({ page }, { keepPage: true })}
          onPageSizeChange={(size) => params.update({ page_size: size })}
        />
      ) : null}
    </div>
  )
}
