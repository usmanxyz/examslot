export function getDashboard(api, signal) {
  return api.get('/admin/dashboard', { signal })
}
