import { useCallback, useState } from 'react'
import { Link } from 'react-router'

import Button from '../../components/ui/Button'
import DataTable from '../../components/ui/DataTable'
import EmptyState from '../../components/ui/EmptyState'
import ErrorState from '../../components/ui/ErrorState'
import PageHeader from '../../components/ui/PageHeader'
import Pagination from '../../components/ui/Pagination'
import StatusPill from '../../components/ui/StatusPill'
import DecisionDialog from '../../features/admin/DecisionDialog'
import ListToolbar from '../../features/admin/ListToolbar'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useListParams } from '../../hooks/useListParams'
import { useQuery } from '../../hooks/useQuery'
import { approveRequest, listRequests, rejectRequest } from '../../services/admin/requestService'
import { formatDateShort } from '../../lib/format'

const STATUS_FILTER = [
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
]

const TYPE_FILTER = [
  { value: 'branch_change', label: 'Branch change' },
  { value: 'date_sheet_change', label: 'Date sheet change' },
]

const TYPE_LABELS = {
  branch_change: 'Branch change',
  date_sheet_change: 'Date sheet change',
}

function shorten(reason) {
  return reason.length > 80 ? `${reason.slice(0, 80)}...` : reason
}

export default function RequestsPage() {
  useDocumentTitle('Requests')
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const params = useListParams({ sort: 'created_at', order: 'desc', filters: ['status', 'type'] })
  const [decision, setDecision] = useState(null)

  const query = params.queryString
  const load = useCallback((signal) => listRequests(api, query, signal), [api, query])
  const { status, data, error, reload } = useQuery(load)

  const rows = data?.items ?? []
  const searching = Boolean(params.q || params.activeFilterCount)

  const columns = [
    {
      key: 'student',
      header: 'Student',
      primary: true,
      cell: (row) => (
        <Link to={`/admin/students/${row.student.id}`} className="text-primary">
          {row.student.full_name} <span className="tabular">{row.student.registration_no}</span>
        </Link>
      ),
    },
    { key: 'type', header: 'Type', cell: (row) => TYPE_LABELS[row.type] },
    { key: 'reason', header: 'Reason', cell: (row) => shorten(row.reason) },
    { key: 'raised', header: 'Raised', sort: 'created_at', cell: (row) => <span className="tabular">{formatDateShort(row.created_at)}</span> },
    { key: 'status', header: 'Status', cell: (row) => <StatusPill status={row.status} /> },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Requests" meta="Students asking to change a branch or a saved date sheet." />

      <ListToolbar
        search={{
          label: 'Search requests',
          placeholder: 'Search student name or registration number',
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
            id: 'filter-type',
            label: 'Type',
            allLabel: 'All types',
            value: params.filters.type,
            onChange: (value) => params.update({ type: value }),
            options: TYPE_FILTER,
          },
        ]}
        activeFilterCount={params.activeFilterCount}
        onClear={params.clearFilters}
      />

      {status === 'error' ? <ErrorState message={error?.message} onRetry={reload} /> : null}

      {status !== 'error' ? (
        <DataTable
          caption="Change requests"
          columns={columns}
          rows={rows}
          rowKey={(row) => row.id}
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
              <EmptyState title="No requests" body="When a student asks for a change, it appears here." />
            )
          }
          actions={(row) =>
            row.status === 'pending' ? (
              <div className="flex flex-wrap justify-end gap-2">
                <Button size="sm" onClick={() => setDecision({ decision: 'approve', request: row })}>
                  Approve
                </Button>
                <Button
                  size="sm"
                  variant="dangerOutline"
                  onClick={() => setDecision({ decision: 'reject', request: row })}
                >
                  Reject
                </Button>
              </div>
            ) : (
              <Link to={`/admin/students/${row.student.id}`} className="text-base text-primary">
                View student
              </Link>
            )
          }
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

      {decision ? (
        <DecisionDialog
          open
          decision={decision.decision}
          request={decision.request}
          onClose={() => setDecision(null)}
          onDecide={(remark) =>
            decision.decision === 'approve'
              ? approveRequest(api, decision.request.id, remark)
              : rejectRequest(api, decision.request.id, remark)
          }
          onDecided={() => {
            showToast(decision.decision === 'approve' ? 'Request approved.' : 'Request rejected.')
            setDecision(null)
            reload()
          }}
        />
      ) : null}
    </div>
  )
}
