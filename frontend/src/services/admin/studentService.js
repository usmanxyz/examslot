export function listStudents(api, query, signal) {
  return api.get(`/admin/students?${query}`, { signal })
}

export function getStudent(api, studentId, signal) {
  return api.get(`/admin/students/${studentId}`, { signal })
}

export function createStudent(api, body) {
  return api.post('/admin/students', body)
}

export function updateStudent(api, studentId, body) {
  return api.patch(`/admin/students/${studentId}`, body)
}

export function deactivateStudent(api, studentId) {
  return api.post(`/admin/students/${studentId}/deactivate`)
}

export function reactivateStudent(api, studentId) {
  return api.post(`/admin/students/${studentId}/reactivate`)
}

export function deleteStudent(api, studentId, confirm) {
  return api.del(`/admin/students/${studentId}?confirm=${encodeURIComponent(confirm)}`)
}

export function sendSetupEmail(api, studentId) {
  return api.post(`/admin/students/${studentId}/setup-email`)
}

export function uploadStudentPhoto(api, studentId, bytes, type) {
  return api.putBytes(`/admin/students/${studentId}/photo`, bytes, type)
}

export function deleteStudentPhoto(api, studentId) {
  return api.del(`/admin/students/${studentId}/photo`)
}

export function getStudentDateSheet(api, studentId, signal) {
  return api.get(`/admin/students/${studentId}/date-sheet`, { signal })
}

export function getStudentRequests(api, studentId, signal) {
  return api.get(`/admin/students/${studentId}/requests?page=1&page_size=50`, { signal })
}
