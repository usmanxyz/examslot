export function listBranches(api, query, signal) {
  return api.get(`/admin/branches?${query}`, { signal })
}

export function createBranch(api, body) {
  return api.post('/admin/branches', body)
}

export function updateBranch(api, branchId, body) {
  return api.patch(`/admin/branches/${branchId}`, body)
}

export function deleteBranch(api, branchId) {
  return api.del(`/admin/branches/${branchId}`)
}
