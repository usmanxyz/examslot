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
import BranchDialog from '../../features/admin/BranchDialog'
import ListToolbar from '../../features/admin/ListToolbar'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useListParams } from '../../hooks/useListParams'
import { useMutation } from '../../hooks/useMutation'
import { useQuery } from '../../hooks/useQuery'
import {
  createBranch,
  deleteBranch,
  listBranches,
  updateBranch,
} from '../../services/admin/branchService'
import { formatPhone } from '../../lib/format'

const STATUS_FILTER = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

export default function BranchesPage() {
  useDocumentTitle('Branches')
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const params = useListParams({ sort: 'code', order: 'asc', filters: ['status'] })
  const [dialog, setDialog] = useState(null)
  const [toDelete, setToDelete] = useState(null)
  const [deleteError, setDeleteError] = useState(null)

  const query = params.queryString
  const load = useCallback((signal) => listBranches(api, query, signal), [api, query])
  const { status, data, error, reload } = useQuery(load)
  const removal = useMutation((branchId) => deleteBranch(api, branchId))

  const rows = data?.items ?? []
  const searching = Boolean(params.q || params.activeFilterCount)

  const onDelete = async () => {
    setDeleteError(null)
    const result = await removal.run(toDelete.id)
    if (result.ok) {
      setToDelete(null)
      showToast('Branch deleted.')
      reload()
      return
    }
    setDeleteError(
      result.error?.code === 'BRANCH_IN_USE'
        ? `${result.error.message} ${result.error.details?.student_count ?? 0} students use this branch.`
        : result.error?.message,
    )
  }

  const columns = [
    { key: 'code', header: 'Code', sort: 'code', primary: true, cell: (row) => <span className="tabular">{row.code}</span> },
    { key: 'name', header: 'Name', sort: 'name', cell: (row) => row.name },
    { key: 'city', header: 'City', sort: 'city', cell: (row) => row.city },
    { key: 'contact', header: 'Contact', cell: (row) => <span className="tabular">{formatPhone(row.contact_phone)}</span> },
    { key: 'students', header: 'Students', cell: (row) => <span className="tabular">{row.student_count}</span> },
    { key: 'status', header: 'Status', cell: (row) => <StatusPill status={row.status} /> },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Branches" meta="Campuses where students can sit their exams.">
        <Button variant="secondary" onClick={() => setDialog({ branch: null })}>
          Add branch
        </Button>
      </PageHeader>

      <ListToolbar
        search={{
          label: 'Search branches',
          placeholder: 'Search code, name or city',
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
          caption="Branches"
          columns={columns}
          rows={rows}
          rowKey={(row) => row.id}
          cardTitle={(row) => `${row.code} ${row.name}`}
          loading={status === 'loading'}
          sort={params.sort}
          order={params.order}
          onSort={params.toggleSort}
          empty={
            searching ? (
              <EmptyState
                title="No results for that search"
                body="Check the spelling or clear the filters."
              >
                <Button variant="secondary" onClick={params.clearFilters}>
                  Clear filters
                </Button>
              </EmptyState>
            ) : (
              <EmptyState
                title="No branches yet"
                body="Add the first campus where students can sit exams."
              >
                <Button onClick={() => setDialog({ branch: null })}>Add branch</Button>
              </EmptyState>
            )
          }
          actions={(row) => (
            <OverflowMenu
              label={`Actions for ${row.code}`}
              items={[
                { label: 'Edit', onSelect: () => setDialog({ branch: row }) },
                {
                  label: row.status === 'active' ? 'Set inactive' : 'Set active',
                  onSelect: async () => {
                    await updateBranch(api, row.id, {
                      status: row.status === 'active' ? 'inactive' : 'active',
                    })
                    showToast('Changes saved.')
                    reload()
                  },
                },
                {
                  label: 'Delete',
                  danger: true,
                  disabled: row.student_count > 0,
                  disabledReason: 'Students use this branch.',
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
        <BranchDialog
          open
          branch={dialog.branch}
          onClose={() => setDialog(null)}
          onSave={(body) =>
            dialog.branch ? updateBranch(api, dialog.branch.id, body) : createBranch(api, body)
          }
          onSaved={() => {
            setDialog(null)
            showToast(dialog.branch ? 'Changes saved.' : 'Branch added.')
            reload()
          }}
        />
      ) : null}

      <ConfirmDialog
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={onDelete}
        title="Delete this branch?"
        body={
          deleteError ??
          `${toDelete?.name ?? ''} will be removed. This cannot be undone.`
        }
        confirmLabel="Delete"
        confirmVariant="danger"
        pending={removal.pending}
        pendingLabel="Deleting"
      />
    </div>
  )
}
