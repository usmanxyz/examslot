export function getMe(api, signal) {
  return api.get('/student/me', { signal })
}

export function changeStudentPassword(api, body) {
  return api.post('/student/me/password', body)
}
