export function studentLogin(api, body) {
  return api.post('/auth/student/login', { ...body, website: '' })
}

export function studentLogout(api) {
  return api.post('/auth/student/logout')
}

export function forgotPassword(api, email) {
  return api.post('/auth/password/forgot', { email, website: '' })
}

export function verifyLink(api, token, signal) {
  return api.post('/auth/password/verify-link', { token }, { signal })
}

export function setPassword(api, token, password) {
  return api.post('/auth/password/set', { token, password, website: '' })
}

export function adminLogin(api, body) {
  return api.post('/auth/admin/login', { ...body, website: '' })
}

export function adminLogout(api) {
  return api.post('/auth/admin/logout')
}
