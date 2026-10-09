export function getPlanner(api, signal) {
  return api.get('/student/planner', { signal })
}

export function saveDateSheet(api, entries) {
  return api.put('/student/date-sheet', { entries })
}
