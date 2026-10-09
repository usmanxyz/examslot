import { useCallback, useEffect, useState } from 'react'

import Button from '../../components/ui/Button'
import ConfirmDialog from '../../components/ui/ConfirmDialog'
import DataTable from '../../components/ui/DataTable'
import EmptyState from '../../components/ui/EmptyState'
import ErrorState from '../../components/ui/ErrorState'
import Field from '../../components/ui/Field'
import OverflowMenu from '../../components/ui/OverflowMenu'
import PageHeader from '../../components/ui/PageHeader'
import Pagination from '../../components/ui/Pagination'
import StatusPill from '../../components/ui/StatusPill'
import TextInput from '../../components/ui/TextInput'
import ListToolbar from '../../features/admin/ListToolbar'
import SlotDialog from '../../features/admin/SlotDialog'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useListParams } from '../../hooks/useListParams'
import { useMutation } from '../../hooks/useMutation'
import { useQuery } from '../../hooks/useQuery'
import { listCourses } from '../../services/admin/courseService'
import { createSlot, deleteSlot, listSlots, updateSlot } from '../../services/admin/slotService'
import { formatClockTime, formatDateShort } from '../../lib/format'

const WHEN_FILTER = [
  { value: 'upcoming', label: 'Upcoming' },
  { value: 'past', label: 'Past' },
  { value: 'all', label: 'All dates' },
]

export default function SlotsPage() {
  useDocumentTitle('Exam slots')
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const params = useListParams({
    sort: 'starts_at',
    order: 'asc',
    filters: ['course_id', 'date_from', 'date_to', 'when'],
  })
  const [dialog, setDialog] = useState(null)
  const [toDelete, setToDelete] = useState(null)
  const [deleteError, setDeleteError] = useState(null)
  const [courses, setCourses] = useState([])

  const query = params.queryString
  const load = useCallback((signal) => listSlots(api, query, signal), [api, query])
  const { status, data, error, reload } = useQuery(load)
  const removal = useMutation((slotId) => deleteSlot(api, slotId))

  useEffect(() => {
    const controller = new AbortController()
    listCourses(api, 'page=1&page_size=100&status=active&sort=code&order=asc', controller.signal)
      .then((result) => setCourses(result.items))
      .catch(() => setCourses([]))
    return () => controller.abort()
  }, [api])

  const rows = data?.items ?? []
  const searching = Boolean(params.q || params.activeFilterCount)

  const onDelete = async () => {
    setDeleteError(null)
    const result = await removal.run(toDelete.id)
    if (result.ok) {
      setToDelete(null)
      showToast('Exam slot deleted.')
      reload()
      return
    }
    setDeleteError(
      result.error?.code === 'SLOT_IN_USE'
        ? `${result.error.message} ${result.error.details?.chosen_count ?? 0} students chose this slot.`
        : result.error?.message,
    )
  }

  const columns = [
    {
      key: 'course',
      header: 'Course',
      sort: 'course_code',
      primary: true,
      cell: (row) => (
        <span>
          <span className="tabular font-medium">{row.course.code}</span> {row.course.title}
        </span>
      ),
    },
    { key: 'date', header: 'Date', sort: 'starts_at', cell: (row) => <span className="tabular">{formatDateShort(row.date)} {row.day}</span> },
    {
      key: 'time',
      header: 'Time',
      cell: (row) => (
        <span className="tabular">
          {formatClockTime(row.start_time)} to {formatClockTime(row.end_time)}
          {row.end_time_set ? '' : ' (default)'}
        </span>
      ),
    },
    { key: 'seats', header: 'Seats per branch', cell: (row) => <span className="tabular">{row.seats_per_branch}</span> },
    { key: 'chosen', header: 'Chosen', cell: (row) => <span className="tabular">{row.chosen_count}</span> },
    {
      key: 'status',
      header: 'Status',
      cell: (row) => <StatusPill status={row.is_past ? 'past' : row.chosen_count > 0 ? 'in_use' : 'upcoming'} />,
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Exam slots" meta="The times students can choose for each course.">
        <Button variant="secondary" onClick={() => setDialog({ slot: null })}>
          Add exam slot
        </Button>
      </PageHeader>

      <div className="space-y-3">
        <ListToolbar
          search={{
            label: 'Search slots',
            placeholder: 'Search course code or title',
            value: params.q,
            onChange: (value) => params.update({ q: value }),
          }}
          filters={[
            {
              id: 'filter-course',
              label: 'Course',
              allLabel: 'All courses',
              value: params.filters.course_id,
              onChange: (value) => params.update({ course_id: value }),
              options: courses.map((course) => ({ value: course.id, label: course.code })),
            },
            {
              id: 'filter-when',
              label: 'When',
              allLabel: 'Upcoming',
              value: params.filters.when,
              onChange: (value) => params.update({ when: value }),
              options: WHEN_FILTER,
            },
          ]}
          activeFilterCount={params.activeFilterCount}
          onClear={params.clearFilters}
        />
        <div className="flex flex-wrap gap-3">
          <div className="w-[11rem]">
            <Field id="date-from" label="From date">
              {(props) => (
                <TextInput
                  {...props}
                  type="date"
                  value={params.filters.date_from}
                  onChange={(event) => params.update({ date_from: event.target.value })}
                />
              )}
            </Field>
          </div>
          <div className="w-[11rem]">
            <Field id="date-to" label="To date">
              {(props) => (
                <TextInput
                  {...props}
                  type="date"
                  value={params.filters.date_to}
                  onChange={(event) => params.update({ date_to: event.target.value })}
                />
              )}
            </Field>
          </div>
        </div>
      </div>

      {status === 'error' ? <ErrorState message={error?.message} onRetry={reload} /> : null}

      {status !== 'error' ? (
        <DataTable
          caption="Exam slots"
          columns={columns}
          rows={rows}
          rowKey={(row) => row.id}
          cardTitle={(row) => `${row.course.code} ${formatDateShort(row.date)}`}
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
              <EmptyState
                title="No exam slots yet"
                body="Add at least one time for each course so students can plan."
              >
                <Button onClick={() => setDialog({ slot: null })}>Add exam slot</Button>
              </EmptyState>
            )
          }
          actions={(row) => (
            <OverflowMenu
              label={`Actions for ${row.course.code} on ${formatDateShort(row.date)}`}
              items={[
                { label: 'Edit', onSelect: () => setDialog({ slot: row }) },
                {
                  label: 'Delete',
                  danger: true,
                  disabled: row.chosen_count > 0,
                  disabledReason: 'Students have chosen this slot.',
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
        <SlotDialog
          open
          slot={dialog.slot}
          courses={courses}
          onClose={() => setDialog(null)}
          onSave={(body) => (dialog.slot ? updateSlot(api, dialog.slot.id, body) : createSlot(api, body))}
          onSaved={() => {
            setDialog(null)
            showToast(dialog.slot ? 'Changes saved.' : 'Exam slot added.')
            reload()
          }}
        />
      ) : null}

      <ConfirmDialog
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={onDelete}
        title="Delete this exam slot?"
        body={deleteError ?? 'Students will no longer see this time. This cannot be undone.'}
        confirmLabel="Delete"
        confirmVariant="danger"
        pending={removal.pending}
        pendingLabel="Deleting"
      />
    </div>
  )
}
