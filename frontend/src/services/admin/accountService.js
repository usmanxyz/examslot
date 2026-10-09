export function getAdmin(api, signal) {
  return api.get('/admin/me', { signal })
}
