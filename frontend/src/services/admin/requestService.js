export function listRequests(api, params, signal) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) query.set(key, String(value))
  })
  return api.get(`/admin/requests?${query.toString()}`, { signal })
}

export function approveRequest(api, requestId, remark) {
  return api.post(`/admin/requests/${requestId}/approve`, { remark })
}

export function rejectRequest(api, requestId, remark) {
  return api.post(`/admin/requests/${requestId}/reject`, { remark })
}
