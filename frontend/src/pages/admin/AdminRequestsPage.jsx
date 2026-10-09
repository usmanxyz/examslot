import { useCallback, useState } from 'react'

import Button from '../../components/ui/Button'
import EmptyState from '../../components/ui/EmptyState'
import ErrorState from '../../components/ui/ErrorState'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import StatusPill from '../../components/ui/StatusPill'
import FormAlert from '../../features/auth/FormAlert'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useMutation } from '../../hooks/useMutation'
import { useQuery } from '../../hooks/useQuery'
import { approveRequest, listRequests, rejectRequest } from '../../services/admin/requestService'
import { formatDateTime, titleCase } from '../../lib/format'

export default function AdminRequestsPage() {
  useDocumentTitle('Requests')
  const { api } = useAdminAuth()
  const { showToast } = useToast()
  const [alert, setAlert] = useState(null)
  const [actingId, setActingId] = useState(null)

  const load = useCallback(
    (signal) => listRequests(api, { page: 1, page_size: 50, status: 'pending' }, signal),
    [api],
  )
  const requests = useQuery(load)
  const { run, pending } = useMutation(({ decide, requestId }) => decide(api, requestId, ''))

  const decide = async (request, action, successMessage) => {
    setAlert(null)
    setActingId(request.id)
    const result = await run({ decide: action, requestId: request.id })
    setActingId(null)
    if (result.ok) {
      showToast(successMessage)
      requests.reload()
      return
    }
    if (result.error) setAlert(result.error.message)
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Requests" meta="Pending branch and date sheet change requests." />

      <FormAlert message={alert} />

      {requests.status === 'loading' ? (
        <div aria-busy="true" className="space-y-3">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
      ) : null}

      {requests.status === 'error' ? (
        <ErrorState
          variant={requests.error?.code === 'NETWORK_ERROR' ? 'network' : 'server'}
          message={requests.error?.message}
          onRetry={requests.reload}
        />
      ) : null}

      {requests.status === 'success' && requests.data.items.length === 0 ? (
        <EmptyState
          title="No pending requests."
          body="When a student asks for a change, it appears here."
        />
      ) : null}

      {requests.status === 'success' && requests.data.items.length > 0 ? (
        <ul className="space-y-3">
          {requests.data.items.map((request) => (
            <li key={request.id} className="space-y-3 rounded-xl border border-line bg-surface p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-[17px] leading-6 font-semibold text-ink">
                    {request.student.full_name}
                  </p>
                  <p className="tabular text-sm text-muted">
                    {`${request.student.registration_no} · ${titleCase(request.type)} · ${formatDateTime(request.created_at)}`}
                  </p>
                </div>
                <StatusPill status={request.status} />
              </div>

              <p className="text-base text-ink">{request.reason}</p>

              <div className="flex flex-wrap gap-3">
                <Button
                  size="sm"
                  pending={pending && actingId === request.id}
                  pendingLabel="Saving"
                  onClick={() => decide(request, approveRequest, 'Request approved.')}
                >
                  Approve
                </Button>
                <Button
                  variant="dangerOutline"
                  size="sm"
                  disabled={pending && actingId === request.id}
                  onClick={() => decide(request, rejectRequest, 'Request rejected.')}
                >
                  Reject
                </Button>
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
