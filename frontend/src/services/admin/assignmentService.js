export function listAssignments(api, query, signal) {
  return api.get(`/admin/assignments?${query}`, { signal })
}

export function getStudentAssignments(api, studentId, signal) {
  return api.get(`/admin/students/${studentId}/assignments`, { signal })
}

export function saveStudentAssignments(api, studentId, courseIds) {
  return api.put(`/admin/students/${studentId}/assignments`, { course_ids: courseIds })
}
