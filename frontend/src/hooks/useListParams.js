import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router'

const PAGE_SIZES = [10, 20, 50]

export function useListParams({ sort: defaultSort, order: defaultOrder = 'asc', filters = [] }) {
  const [searchParams, setSearchParams] = useSearchParams()

  const page = Math.max(1, Number(searchParams.get('page')) || 1)
  const rawSize = Number(searchParams.get('page_size'))
  const pageSize = PAGE_SIZES.includes(rawSize) ? rawSize : 20
  const q = searchParams.get('q') ?? ''
  const sort = searchParams.get('sort') ?? defaultSort
  const order = searchParams.get('order') === 'desc' ? 'desc' : searchParams.get('order') === 'asc' ? 'asc' : defaultOrder

  const filterValues = useMemo(
    () => Object.fromEntries(filters.map((name) => [name, searchParams.get(name) ?? ''])),
    [filters, searchParams],
  )

  const update = useCallback(
    (changes, { keepPage = false } = {}) => {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current)
          Object.entries(changes).forEach(([key, value]) => {
            if (value === '' || value === null || value === undefined) next.delete(key)
            else next.set(key, String(value))
          })
          if (!keepPage && !('page' in changes)) next.delete('page')
          return next
        },
        { replace: true },
      )
    },
    [setSearchParams],
  )

  const clearFilters = useCallback(() => {
    update(Object.fromEntries([...filters, 'q'].map((name) => [name, ''])))
  }, [filters, update])

  const activeFilterCount = filters.filter((name) => filterValues[name]).length

  const queryString = useMemo(() => {
    const query = new URLSearchParams()
    query.set('page', String(page))
    query.set('page_size', String(pageSize))
    if (q.trim()) query.set('q', q.trim())
    if (sort) {
      query.set('sort', sort)
      query.set('order', order)
    }
    filters.forEach((name) => {
      if (filterValues[name]) query.set(name, filterValues[name])
    })
    return query.toString()
  }, [page, pageSize, q, sort, order, filters, filterValues])

  const toggleSort = useCallback(
    (column) => {
      if (column === sort) {
        update({ sort: column, order: order === 'asc' ? 'desc' : 'asc' })
        return
      }
      update({ sort: column, order: 'asc' })
    },
    [sort, order, update],
  )

  return {
    page,
    pageSize,
    q,
    sort,
    order,
    filters: filterValues,
    activeFilterCount,
    queryString,
    update,
    clearFilters,
    toggleSort,
    pageSizes: PAGE_SIZES,
  }
}
