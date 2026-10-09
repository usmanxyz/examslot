import { useCallback } from 'react'

import Disclosure from '../../components/ui/Disclosure'
import EmptyState from '../../components/ui/EmptyState'
import ErrorState from '../../components/ui/ErrorState'
import Skeleton from '../../components/ui/Skeleton'
import Planner from '../../features/student/Planner'
import SavedSummary from '../../features/student/SavedSummary'
import StudentRecord from '../../features/student/StudentRecord'
import { useStudentAuth } from '../../context/StudentAuthContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { useQuery } from '../../hooks/useQuery'
import { getPlanner } from '../../services/student/plannerService'

const TITLES = {
  assignment_incomplete: 'Your courses are on the way',
  branch_required: 'Plan your exams',
  planning: 'Plan your exams',
  reopened: 'Change your date sheet',
  saved: 'Your exams are planned',
}

function savedEntries(courses) {
  return courses
    .map((entry) => {
      const slot = entry.slots.find((item) => item.id === entry.selected_slot_id)
      return slot
        ? {
            courseId: entry.course.id,
            courseCode: entry.course.code,
            starts_at: slot.starts_at,
            ends_at: slot.ends_at,
            end_time_set: slot.end_time_set,
          }
        : null
    })
    .filter(Boolean)
}

export default function DashboardPage() {
  const { api, me } = useStudentAuth()
  const load = useCallback((signal) => getPlanner(api, signal), [api])
  const planner = useQuery(load)
  const state = planner.data?.state ?? 'planning'
  useDocumentTitle(TITLES[state])

  const identity = me
    ? [me.full_name, me.registration_no, me.program, me.branch?.name].filter(Boolean).join(' · ')
    : ''

  return (
    <div className="space-y-6">
      {state === 'reopened' ? (
        <p role="status" className="rounded-xl bg-warning-soft px-4 py-3 text-base text-warning">
          Your date sheet change was approved. You can change your exam times once.
        </p>
      ) : null}

      <div className="space-y-2">
        <h1 className="font-serif text-[28px] leading-9 font-semibold tracking-[-0.01em] sm:text-[34px] sm:leading-[42px]">
          {TITLES[state]}
        </h1>
        {me ? <p className="tabular text-[15px] text-muted">{identity}</p> : null}
      </div>

      <section aria-labelledby="record-heading" className="border-t border-line pt-4">
        <h2 id="record-heading" className="text-[17px] leading-6 font-semibold text-ink">
          Your record
        </h2>
        {me ? (
          <>
            <div className="lg:hidden">
              <Disclosure summary="Your record: personal, guardian and academic details">
                <StudentRecord me={me} />
              </Disclosure>
            </div>
            <div className="hidden lg:block">
              <StudentRecord me={me} />
            </div>
          </>
        ) : null}
      </section>

      <section aria-labelledby="planner-heading" className="mt-10 lg:mt-16">
        <h2 id="planner-heading" className="text-xl leading-7 font-semibold text-ink">
          {state === 'saved' ? 'Your exams' : 'Choose a time for each course'}
        </h2>
        <p className="text-[13px] leading-[18px] text-muted">All times are Pakistan time.</p>

        <div className="mt-6">
          {planner.status === 'loading' ? (
            <div aria-busy="true" className="space-y-3">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : null}

          {planner.status === 'error' ? (
            <ErrorState
              variant={planner.error?.code === 'NETWORK_ERROR' ? 'network' : 'server'}
              onRetry={planner.reload}
            />
          ) : null}

          {planner.status === 'success' && state === 'assignment_incomplete' ? (
            <EmptyState
              title="Your courses have not been assigned yet."
              body="Your exam office will assign 4 to 6 courses. Check back later."
            />
          ) : null}

          {planner.status === 'success' && state === 'saved' ? (
            <SavedSummary entries={savedEntries(planner.data.courses)} />
          ) : null}

          {planner.status === 'success' && (state === 'planning' || state === 'reopened') ? (
            <Planner
              data={planner.data}
              branchName={me?.branch?.name ?? ''}
              studentId={me?.id ?? 'student'}
            />
          ) : null}
        </div>
      </section>
    </div>
  )
}
