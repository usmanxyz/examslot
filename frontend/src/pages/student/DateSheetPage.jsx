import { useCallback, useState } from 'react'
import { Download, Printer } from 'lucide-react'

import Button from '../../components/ui/Button'
import DefinitionList from '../../components/ui/DefinitionList'
import ErrorState from '../../components/ui/ErrorState'
import Skeleton from '../../components/ui/Skeleton'
import DateSheetTable from '../../features/student/DateSheetTable'
import FormAlert from '../../features/auth/FormAlert'
import { useStudentAuth } from '../../context/StudentAuthContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useMutation } from '../../hooks/useMutation'
import { useQuery } from '../../hooks/useQuery'
import { getDateSheet, getDateSheetPdf } from '../../services/student/dateSheetService'
import { formatDateShort, formatTime } from '../../lib/format'

function detailItems(data) {
  return [
    { term: 'Name', value: data.student.full_name },
    { term: 'Registration number', value: data.student.registration_no },
    { term: 'Program', value: data.student.program },
    { term: 'Semester and session', value: `Semester ${data.student.semester}, ${data.student.session}` },
    { term: 'Exam branch', value: `${data.branch.name}, ${data.branch.city}` },
    { term: 'Branch address', value: data.branch.address },
  ]
}

export default function DateSheetPage() {
  useDocumentTitle('Your date sheet')
  const { api } = useStudentAuth()
  const [printedAt] = useState(() => new Date().toISOString())
  const [alert, setAlert] = useState(null)
  const load = useCallback((signal) => getDateSheet(api, signal), [api])
  const sheet = useQuery(load)
  const { run, pending } = useMutation(() => getDateSheetPdf(api))

  const onDownload = async () => {
    setAlert(null)
    const result = await run()
    if (!result.ok) {
      if (result.error) setAlert(result.error.message)
      return
    }
    const url = URL.createObjectURL(result.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `examslot-date-sheet-${sheet.data.student.registration_no}.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  if (sheet.status === 'loading') {
    return (
      <div aria-busy="true" className="space-y-6">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  if (sheet.status === 'error') {
    const code = sheet.error?.code
    if (code === 'DATE_SHEET_NOT_SAVED') {
      return <ErrorState variant="notFound" message="You have not saved a date sheet yet." />
    }
    return (
      <ErrorState variant={code === 'NETWORK_ERROR' ? 'network' : 'server'} onRetry={sheet.reload} />
    )
  }

  const data = sheet.data

  return (
    <div className="print-sheet space-y-6">
      <div className="print-hidden flex flex-wrap items-end justify-between gap-4">
        <h1 className="font-serif text-[28px] leading-9 font-semibold tracking-[-0.01em] sm:text-[34px] sm:leading-[42px]">
          Your date sheet
        </h1>
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="secondary" onClick={() => window.print()}>
            <Printer size={20} strokeWidth={1.75} aria-hidden="true" />
            Print
          </Button>
         
        </div>
      </div>

      <div className="print-only">
        <p className="print-brand">ExamSlot</p>
        <p className="print-title">Examination date sheet</p>
      </div>

      <FormAlert message={alert} />

      <div className="print-details">
        <DefinitionList items={detailItems(data)} columns={2} />
      </div>

      <DateSheetTable entries={data.entries} />

      <p className="tabular print-hidden text-[13px] leading-[18px] text-muted">
        {`Saved on ${formatDateShort(data.saved_at)} at ${formatTime(data.saved_at)}. All times are Pakistan time.`}
      </p>

      <p className="tabular print-footer print-only">
        {`Saved on ${formatDateShort(data.saved_at)}, ${formatTime(data.saved_at)} (Pakistan time). Printed on ${formatDateShort(printedAt)}, ${formatTime(printedAt)}.`}
      </p>
    </div>
  )
}
