export function listRequests(api, signal) {
  return api.get('/student/requests?page=1&page_size=50', { signal })
}

export function createRequest(api, body) {
  return api.post('/student/requests', body)
}
