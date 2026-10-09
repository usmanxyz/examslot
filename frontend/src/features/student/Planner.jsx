import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'

import AgendaRail from './AgendaRail'
import PlannerBar from './PlannerBar'
import PlannerCourse from './PlannerCourse'
import ReviewDialog from './ReviewDialog'
import { useStudentAuth } from '../../context/StudentAuthContext'
import { useToast } from '../../context/ToastContext'
import { useMutation } from '../../hooks/useMutation'
import { formatDateWithoutYear, formatTime } from '../../lib/format'
import { alternativesFor, overlaps } from '../../lib/overlap'
import { PLANNER_DRAFT_KEY, readStored, removeStored, writeStored } from '../../lib/storage'
import { saveDateSheet } from '../../services/student/plannerService'

function draftKey(studentId) {
  return `${PLANNER_DRAFT_KEY}.${studentId}`
}

function initialPicks(courses, studentId) {
  const draft = readStored(window.sessionStorage, draftKey(studentId)) ?? {}
  return Object.fromEntries(
    courses.map((entry) => {
      const drafted = draft[entry.course.id]
      const valid = entry.slots.some((slot) => slot.id === drafted)
      return [entry.course.id, entry.fixed || !valid ? entry.selected_slot_id : drafted]
    }),
  )
}

export default function Planner({ data, branchName, studentId }) {
  const { api, refreshMe } = useStudentAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const [picksMap, setPicksMap] = useState(() => initialPicks(data.courses, studentId))
  const [openId, setOpenId] = useState(null)
  const [reviewing, setReviewing] = useState(false)
  const [alert, setAlert] = useState(null)
  const [issues, setIssues] = useState({})
  const { run, pending } = useMutation((entries) => saveDateSheet(api, entries))

  useEffect(() => {
    writeStored(window.sessionStorage, draftKey(studentId), picksMap)
  }, [picksMap, studentId])

  const picks = useMemo(
    () =>
      data.courses
        .map((entry) => {
          const slot = entry.slots.find((item) => item.id === picksMap[entry.course.id])
          return slot
            ? { courseId: entry.course.id, courseCode: entry.course.code, slot, slots: entry.slots }
            : null
        })
        .filter(Boolean),
    [data.courses, picksMap],
  )

  const total = data.courses.length
  const complete = picks.length === total && total > 0
  const progress = `${picks.length} of ${total} courses planned`
  const firstUnplanned = data.courses.find((entry) => !picksMap[entry.course.id]) ?? null
  const activeId = openId ?? firstUnplanned?.course.id ?? data.courses[0]?.course.id ?? null

  const clashingPick = useCallback(
    (courseId, slot) => picks.find((pick) => pick.courseId !== courseId && overlaps(slot, pick.slot)) ?? null,
    [picks],
  )

  const select = (courseId, slotId) => {
    setIssues({})
    setPicksMap((current) => ({ ...current, [courseId]: slotId }))
  }

  const useAlternative = (courseId, slotId, alternative) => {
    setIssues({})
    setPicksMap((current) => ({
      ...current,
      [alternative.courseId]: alternative.slot.id,
      [courseId]: slotId,
    }))
  }

  const onSave = async () => {
    setAlert(null)
    const entries = picks.map((pick) => ({ course_id: pick.courseId, slot_id: pick.slot.id }))
    const result = await run(entries)
    if (result.ok) {
      removeStored(window.sessionStorage, draftKey(studentId))
      setReviewing(false)
      await refreshMe()
      showToast('Date sheet saved.')
      navigate('/student/date-sheet', { replace: true })
      return
    }
    const error = result.error
    if (!error) return
    const courses = error.details?.courses ?? []
    if (courses.length > 0) {
      setIssues(Object.fromEntries(courses.map((course) => [course.course_id, error.message])))
      setReviewing(false)
      setOpenId(courses[0].course_id)
      return
    }
    setAlert(error.message)
  }

  return (
    <div className="lg:grid lg:grid-cols-12 lg:gap-8">
      <div className="space-y-3 pb-20 lg:col-span-8 lg:pb-0">
        {data.courses.map((entry) => (
          <PlannerCourse
            key={entry.course.id}
            entry={entry}
            open={activeId === entry.course.id}
            focal={firstUnplanned?.course.id === entry.course.id}
            selectedSlotId={picksMap[entry.course.id] ?? null}
            issueMessage={issues[entry.course.id] ?? null}
            clashFor={(slot) => {
              if (picksMap[entry.course.id] === slot.id) return null
              const clash = clashingPick(entry.course.id, slot)
              return clash
                ? `Clashes with ${clash.courseCode} on ${formatDateWithoutYear(clash.slot.starts_at)} at ${formatTime(clash.slot.starts_at)}`
                : null
            }}
            alternativesFor={(slot) => {
              if (picksMap[entry.course.id] === slot.id) return []
              const clash = clashingPick(entry.course.id, slot)
              if (!clash) return []
              const avoid = picks
                .filter((pick) => pick.courseId !== clash.courseId && pick.courseId !== entry.course.id)
                .concat([{ courseId: entry.course.id, slot }])
              return alternativesFor(clash, avoid).map((option) => ({
                courseId: clash.courseId,
                courseCode: clash.courseCode,
                slot: option,
              }))
            }}
            onToggle={(courseId) => setOpenId(activeId === courseId ? null : courseId)}
            onSelect={select}
            onUseAlternative={useAlternative}
          />
        ))}
      </div>

      <div className="hidden lg:col-span-4 lg:block">
        <div className="sticky top-6">
          <AgendaRail
            picks={picks}
            progress={progress}
            complete={complete}
            onReview={() => setReviewing(true)}
          />
        </div>
      </div>

      <PlannerBar progress={progress} complete={complete} onReview={() => setReviewing(true)} />

      <ReviewDialog
        open={reviewing}
        onClose={() => setReviewing(false)}
        branchName={branchName}
        picks={picks}
        pending={pending}
        alert={alert}
        onSave={onSave}
      />
    </div>
  )
}
