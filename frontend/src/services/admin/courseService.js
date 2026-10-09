export function listCourses(api, query, signal) {
  return api.get(`/admin/courses?${query}`, { signal })
}

export function createCourse(api, body) {
  return api.post('/admin/courses', body)
}

export function updateCourse(api, courseId, body) {
  return api.patch(`/admin/courses/${courseId}`, body)
}

export function deleteCourse(api, courseId) {
  return api.del(`/admin/courses/${courseId}`)
}
