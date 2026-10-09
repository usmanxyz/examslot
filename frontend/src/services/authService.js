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
