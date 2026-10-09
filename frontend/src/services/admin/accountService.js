export function getAdminMe(api, signal) {
  return api.get('/admin/me', { signal })
}

export function changeAdminPassword(api, body) {
  return api.post('/admin/me/password', body)
}
