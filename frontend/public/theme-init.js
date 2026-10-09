;(function () {
  var preference
  try {
    preference = window.localStorage.getItem('examslot.theme')
  } catch {
    preference = null
  }
  var resolved = preference
  if (resolved !== 'light' && resolved !== 'dark') {
    resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  document.documentElement.dataset.theme = resolved
})()
