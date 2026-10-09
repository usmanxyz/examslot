export function overlaps(a, b) {
  if (!a || !b) return false
  const aStart = new Date(a.starts_at).getTime()
  const aEnd = new Date(a.ends_at).getTime()
  const bStart = new Date(b.starts_at).getTime()
  const bEnd = new Date(b.ends_at).getTime()
  return aStart < bEnd && bStart < aEnd
}

export function clashesFor(slot, picks) {
  return picks.filter((pick) => pick.slot.id !== slot.id && overlaps(slot, pick.slot))
}

export function alternativesFor(clash, picks, limit = 2) {
  const others = picks.filter((pick) => pick.courseId !== clash.courseId)
  return clash.slots
    .filter((slot) => slot.id !== clash.slot.id)
    .filter((slot) => !others.some((pick) => overlaps(slot, pick.slot)))
    .slice(0, limit)
}
