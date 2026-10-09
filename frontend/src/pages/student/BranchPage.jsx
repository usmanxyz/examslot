import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router'

import Button from '../../components/ui/Button'
import ConfirmDialog from '../../components/ui/ConfirmDialog'
import ErrorState from '../../components/ui/ErrorState'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import BranchChoices from '../../features/student/BranchChoices'
import FormAlert from '../../features/auth/FormAlert'
import { useStudentAuth } from '../../context/StudentAuthContext'
import { useToast } from '../../context/ToastContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useMutation } from '../../hooks/useMutation'
import { useQuery } from '../../hooks/useQuery'
import { listBranches, saveBranch } from '../../services/student/branchService'

const FIRST_TIME =
  'This is where you will sit all your papers. You can choose once. To change it later, you will need an approved request.'
const REOPENED =
  'Your branch change was approved. You can choose a branch once more. Your exam times stay the same.'

export default function BranchPage() {
  useDocumentTitle('Choose your exam branch')
  const { api, me, refreshMe } = useStudentAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const [selectedId, setSelectedId] = useState(null)
  const [confirming, setConfirming] = useState(false)
  const [alert, setAlert] = useState(null)

  const load = useCallback((signal) => listBranches(api, signal), [api])
  const branches = useQuery(load)
  const { run, pending } = useMutation((branchId) => saveBranch(api, branchId))

  if (branches.status === 'loading') {
    return (
      <div aria-busy="true" className="space-y-6">
        <Skeleton className="h-10 w-80" />
        <Skeleton className="h-5 w-full max-w-[36rem]" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  if (branches.status === 'error') {
    const variant = branches.error?.code === 'NETWORK_ERROR' ? 'network' : 'server'
    return <ErrorState variant={variant} onRetry={branches.reload} />
  }

  const items = branches.data.items
  const selected = items.find((branch) => branch.id === selectedId) ?? null

  const onSave = async () => {
    setAlert(null)
    const result = await run(selectedId)
    setConfirming(false)
    if (result.ok) {
      await refreshMe()
      showToast('Branch saved.')
      navigate('/student', { replace: true })
      return
    }
    if (result.error) {
      setAlert(result.error.message)
      branches.reload()
    }
  }

  return (
    <div className="mx-auto max-w-[44rem] space-y-8">
      <PageHeader
        title="Choose your exam branch"
        meta={me?.can_change_branch && me?.branch ? REOPENED : FIRST_TIME}
      />

      {items.length === 0 ? (
        <ErrorState variant="server" message="No exam branches are available yet. Check back later." />
      ) : (
        <>
          <BranchChoices items={items} selectedId={selectedId} onSelect={setSelectedId} />
          <FormAlert message={alert} />
          <Button disabled={!selected} onClick={() => setConfirming(true)}>
            Save branch
          </Button>
        </>
      )}

      <ConfirmDialog
        open={confirming && Boolean(selected)}
        onClose={() => setConfirming(false)}
        onConfirm={onSave}
        title={selected ? `Save ${selected.name} as your exam branch?` : ''}
        body="You can choose once. To change it later, send a request from Need help."
        confirmLabel="Save branch"
        cancelLabel="Go back"
        pending={pending}
        pendingLabel="Saving"
      />
    </div>
  )
}
