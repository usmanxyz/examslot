export function listBranches(api, signal) {
  return api.get('/student/branches', { signal })
}

export function saveBranch(api, branchId) {
  return api.put('/student/branch', { branch_id: branchId })
}
