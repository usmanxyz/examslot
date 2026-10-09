export function listStudents(api, params, signal) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) query.set(key, String(value))
  })
  return api.get(`/admin/students?${query.toString()}`, { signal })
}
