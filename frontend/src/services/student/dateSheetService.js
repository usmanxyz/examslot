export function getDateSheet(api, signal) {
  return api.get('/student/date-sheet', { signal })
}

export function getDateSheetPdf(api) {
  return api.getBlob('/student/date-sheet/pdf')
}
