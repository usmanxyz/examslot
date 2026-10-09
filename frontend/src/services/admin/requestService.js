export function listRequests(api, query, signal) {
  return api.get(`/admin/requests?${query}`, { signal })
}

export function approveRequest(api, requestId, remark) {
  return api.post(`/admin/requests/${requestId}/approve`, { remark })
}

export function rejectRequest(api, requestId, remark) {
  return api.post(`/admin/requests/${requestId}/reject`, { remark })
}
