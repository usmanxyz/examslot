import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'

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
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useListParams } from '../../hooks/useListParams'
import { useMutation } from '../../hooks/useMutation'
import { useQuery } from '../../hooks/useQuery'
import { listBranches } from '../../services/admin/branchService'
import {
  deactivateStudent,
  deleteStudent,
  listStudents,
  reactivateStudent,
  sendSetupEmail,
} from '../../services/admin/studentService'

const ACCOUNT_FILTER = [
  { value: 'invited', label: 'Invited' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

const PROGRESS_FILTER = [
  { value: 'assignment_incomplete', label: 'Assignment incomplete' },
  { value: 'branch_pending', label: 'Branch pending' },
  { value: 'planning', label: 'Planning' },
  { value: 'saved', label: 'Saved' },
]

export default function StudentsPage() {
  useDocumentTitle('Students')
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const params = useListParams({
    sort: 'created_at',
    order: 'desc',
    filters: ['account_status', 'progress', 'branch_id', 'program'],
  })
  const [branches, setBranches] = useState([])
  const [toDelete, setToDelete] = useState(null)
  const [confirmText, setConfirmText] = useState('')
  const [deleteError, setDeleteError] = useState(null)

  const query = params.queryString
  const load = useCallback((signal) => listStudents(api, query, signal), [api, query])
  const { status, data, error, reload } = useQuery(load)
  const removal = useMutation((student) => deleteStudent(api, student.id, confirmText))

  useEffect(() => {
    const controller = new AbortController()
    listBranches(api, 'page=1&page_size=100&sort=code&order=asc', controller.signal)
      .then((result) => setBranches(result.items))
      .catch(() => setBranches([]))
    return () => controller.abort()
  }, [api])

  const rows = data?.items ?? []
  const searching = Boolean(params.q || params.activeFilterCount)

  const onDelete = async () => {
    setDeleteError(null)
    const result = await removal.run(toDelete)
    if (result.ok) {
      setToDelete(null)
      setConfirmText('')
      showToast('Student deleted.')
      reload()
      return
    }
    setDeleteError(result.error?.message)
  }

  const columns = [
    {
      key: 'name',
      header: 'Name',
      sort: 'full_name',
      primary: true,
      cell: (row) => (
        <Link to={`/admin/students/${row.id}`} className="text-primary">
          {row.full_name}
        </Link>
      ),
    },
    {
      key: 'registration_no',
      header: 'Registration no.',
      sort: 'registration_no',
      cell: (row) => <span className="tabular">{row.registration_no}</span>,
    },
    {
      key: 'program',
      header: 'Program and semester',
      cell: (row) => (
        <span>
          {row.program} <span className="tabular text-muted">Semester {row.semester}</span>
        </span>
      ),
    },
    { key: 'branch', header: 'Branch', cell: (row) => (row.branch ? row.branch.code : 'Not chosen') },
    { key: 'progress', header: 'Progress', cell: (row) => <StatusPill status={row.progress} /> },
    { key: 'account', header: 'Account', cell: (row) => <StatusPill status={row.account_status} /> },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Students" meta="Every student the exam office has created.">
        <Button variant="secondary" onClick={() => navigate('/admin/students/new')}>
          Create student
        </Button>
      </PageHeader>

      <div className="space-y-3">
        <ListToolbar
          search={{
            label: 'Search students',
            placeholder: 'Search name, email or registration number',
            value: params.q,
            onChange: (value) => params.update({ q: value }),
          }}
          filters={[
            {
              id: 'filter-account',
              label: 'Account status',
              allLabel: 'All accounts',
              value: params.filters.account_status,
              onChange: (value) => params.update({ account_status: value }),
              options: ACCOUNT_FILTER,
            },
            {
              id: 'filter-progress',
              label: 'Progress',
              allLabel: 'All progress',
              value: params.filters.progress,
              onChange: (value) => params.update({ progress: value }),
              options: PROGRESS_FILTER,
            },
            {
              id: 'filter-branch',
              label: 'Branch',
              allLabel: 'All branches',
              value: params.filters.branch_id,
              onChange: (value) => params.update({ branch_id: value }),
              options: branches.map((branch) => ({ value: branch.id, label: branch.code })),
            },
          ]}
          activeFilterCount={params.activeFilterCount}
          onClear={params.clearFilters}
        />
        <div className="w-full sm:max-w-[16rem]">
          <Field id="filter-program" label="Program">
            {(props) => (
              <TextInput
                {...props}
                value={params.filters.program}
                onChange={(event) => params.update({ program: event.target.value })}
              />
            )}
          </Field>
        </div>
      </div>

      {status === 'error' ? <ErrorState message={error?.message} onRetry={reload} /> : null}

      {status !== 'error' ? (
        <DataTable
          caption="Students"
          columns={columns}
          rows={rows}
          rowKey={(row) => row.id}
          cardTitle={(row) => row.full_name}
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
              <EmptyState title="No students yet" body="Create a student to send their setup email.">
                <Button onClick={() => navigate('/admin/students/new')}>Create student</Button>
              </EmptyState>
            )
          }
          actions={(row) => (
            <OverflowMenu
              label={`Actions for ${row.full_name}`}
              items={[
                { label: 'View', onSelect: () => navigate(`/admin/students/${row.id}`) },
                { label: 'Edit', onSelect: () => navigate(`/admin/students/${row.id}/edit`) },
                { label: 'Assign courses', onSelect: () => navigate(`/admin/assignments/${row.id}`) },
                {
                  label: 'Resend setup email',
                  disabled: row.account_status !== 'invited',
                  disabledReason: 'This student already set a password.',
                  onSelect: async () => {
                    await sendSetupEmail(api, row.id)
                    showToast('Setup email sent.')
                    reload()
                  },
                },
                {
                  label: row.account_status === 'inactive' ? 'Reactivate' : 'Deactivate',
                  onSelect: async () => {
                    if (row.account_status === 'inactive') {
                      await reactivateStudent(api, row.id)
                      showToast('Student reactivated.')
                    } else {
                      await deactivateStudent(api, row.id)
                      showToast('Student deactivated.')
                    }
                    reload()
                  },
                },
                {
                  label: 'Delete',
                  danger: true,
                  onSelect: () => {
                    setDeleteError(null)
                    setConfirmText('')
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

      <ConfirmDialog
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={onDelete}
        title={`Delete ${toDelete?.full_name ?? 'this student'} permanently?`}
        confirmLabel="Delete"
        confirmVariant="danger"
        confirmDisabled={
          confirmText.trim().toUpperCase() !== (toDelete?.registration_no ?? '').toUpperCase()
        }
        pending={removal.pending}
        pendingLabel="Deleting"
      >
        <div className="space-y-4">
          <p className="text-base text-ink">
            This removes the record, courses, date sheet and requests. It cannot be undone.
          </p>
          <Field
            id="delete-confirm"
            label={`Type ${toDelete?.registration_no ?? ''} to confirm`}
            error={deleteError}
          >
            {(props) => (
              <TextInput {...props} value={confirmText} onChange={(event) => setConfirmText(event.target.value)} />
            )}
          </Field>
        </div>
      </ConfirmDialog>
    </div>
  )
}
