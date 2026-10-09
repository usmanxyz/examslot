import { useCallback, useState } from 'react'

import Button from '../../components/ui/Button'
import ConfirmDialog from '../../components/ui/ConfirmDialog'
import DataTable from '../../components/ui/DataTable'
import EmptyState from '../../components/ui/EmptyState'
import ErrorState from '../../components/ui/ErrorState'
import OverflowMenu from '../../components/ui/OverflowMenu'
import PageHeader from '../../components/ui/PageHeader'
import Pagination from '../../components/ui/Pagination'
import StatusPill from '../../components/ui/StatusPill'
import CourseDialog from '../../features/admin/CourseDialog'
import ListToolbar from '../../features/admin/ListToolbar'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useListParams } from '../../hooks/useListParams'
import { useMutation } from '../../hooks/useMutation'
import { useQuery } from '../../hooks/useQuery'
import {
  createCourse,
  deleteCourse,
  listCourses,
  updateCourse,
} from '../../services/admin/courseService'

const STATUS_FILTER = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

export default function CoursesPage() {
  useDocumentTitle('Courses')
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const params = useListParams({ sort: 'code', order: 'asc', filters: ['status', 'department'] })
  const [dialog, setDialog] = useState(null)
  const [toDelete, setToDelete] = useState(null)
  const [deleteError, setDeleteError] = useState(null)

  const query = params.queryString
  const load = useCallback((signal) => listCourses(api, query, signal), [api, query])
  const { status, data, error, reload } = useQuery(load)
  const removal = useMutation((courseId) => deleteCourse(api, courseId))

  const rows = data?.items ?? []
  const searching = Boolean(params.q || params.activeFilterCount)
  const departments = [...new Set(rows.map((row) => row.department))].sort()

  const onDelete = async () => {
    setDeleteError(null)
    const result = await removal.run(toDelete.id)
    if (result.ok) {
      setToDelete(null)
      showToast('Course deleted.')
      reload()
      return
    }
    setDeleteError(result.error?.message)
  }

  const columns = [
    { key: 'code', header: 'Code', sort: 'code', primary: true, cell: (row) => <span className="tabular">{row.code}</span> },
    { key: 'title', header: 'Title', sort: 'title', cell: (row) => row.title },
    { key: 'credits', header: 'Credit hours', cell: (row) => <span className="tabular">{row.credit_hours}</span> },
    { key: 'department', header: 'Department', sort: 'department', cell: (row) => row.department },
    { key: 'assigned', header: 'Assigned', cell: (row) => <span className="tabular">{row.assigned_count}</span> },
    { key: 'slots', header: 'Slots', cell: (row) => <span className="tabular">{row.slot_count}</span> },
    { key: 'status', header: 'Status', cell: (row) => <StatusPill status={row.status} /> },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Courses" meta="The courses students sit exams for.">
        <Button variant="secondary" onClick={() => setDialog({ course: null })}>
          Add course
        </Button>
      </PageHeader>

      <ListToolbar
        search={{
          label: 'Search courses',
          placeholder: 'Search code, title or department',
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
          {
            id: 'filter-department',
            label: 'Department',
            allLabel: 'All departments',
            value: params.filters.department,
            onChange: (value) => params.update({ department: value }),
            options: departments.map((name) => ({ value: name, label: name })),
          },
        ]}
        activeFilterCount={params.activeFilterCount}
        onClear={params.clearFilters}
      />

      {status === 'error' ? <ErrorState message={error?.message} onRetry={reload} /> : null}

      {status !== 'error' ? (
        <DataTable
          caption="Courses"
          columns={columns}
          rows={rows}
          rowKey={(row) => row.id}
          cardTitle={(row) => `${row.code} ${row.title}`}
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
              <EmptyState title="No courses yet" body="Add the courses students will sit exams for.">
                <Button onClick={() => setDialog({ course: null })}>Add course</Button>
              </EmptyState>
            )
          }
          actions={(row) => (
            <OverflowMenu
              label={`Actions for ${row.code}`}
              items={[
                { label: 'Edit', onSelect: () => setDialog({ course: row }) },
                {
                  label: row.status === 'active' ? 'Set inactive' : 'Set active',
                  onSelect: async () => {
                    await updateCourse(api, row.id, {
                      status: row.status === 'active' ? 'inactive' : 'active',
                    })
                    showToast('Changes saved.')
                    reload()
                  },
                },
                {
                  label: 'Delete',
                  danger: true,
                  disabled: row.assigned_count > 0 || row.slot_count > 0,
                  disabledReason: 'This course has assignments or slots.',
                  onSelect: () => {
                    setDeleteError(null)
                    setToDelete(row)
                  },
                },
              ]}
            />
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

      {dialog ? (
        <CourseDialog
          open
          course={dialog.course}
          onClose={() => setDialog(null)}
          onSave={(body) =>
            dialog.course ? updateCourse(api, dialog.course.id, body) : createCourse(api, body)
          }
          onSaved={() => {
            setDialog(null)
            showToast(dialog.course ? 'Changes saved.' : 'Course added.')
            reload()
          }}
        />
      ) : null}

      <ConfirmDialog
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={onDelete}
        title="Delete this course?"
        body={deleteError ?? `${toDelete?.title ?? ''} will be removed. This cannot be undone.`}
        confirmLabel="Delete"
        confirmVariant="danger"
        pending={removal.pending}
        pendingLabel="Deleting"
      />
    </div>
  )
}
