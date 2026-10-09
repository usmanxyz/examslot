export function listSlots(api, query, signal) {
  return api.get(`/admin/slots?${query}`, { signal })
}

export function getSlot(api, slotId, signal) {
  return api.get(`/admin/slots/${slotId}`, { signal })
}

export function createSlot(api, body) {
  return api.post('/admin/slots', body)
}

export function updateSlot(api, slotId, body) {
  return api.patch(`/admin/slots/${slotId}`, body)
}

export function deleteSlot(api, slotId) {
  return api.del(`/admin/slots/${slotId}`)
}
