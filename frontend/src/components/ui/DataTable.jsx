import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'

import Skeleton from './Skeleton'

function SortButton({ column, sort, order, onSort }) {
  const active = sort === column.sort
  const Icon = active ? (order === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown

  return (
    <button
      type="button"
      onClick={() => onSort(column.sort)}
      className="inline-flex min-h-9 items-center gap-1.5 rounded-lg text-sm font-semibold text-ink hover:text-primary"
    >
      {column.header}
      <Icon size={16} strokeWidth={1.75} aria-hidden="true" className={active ? 'text-primary' : 'text-muted'} />
    </button>
  )
}

export default function DataTable({
  caption,
  columns,
  rows,
  rowKey,
  loading = false,
  sort,
  order,
  onSort,
  cardTitle,
  actions,
  empty,
}) {
  if (loading) {
    return (
      <div aria-busy="true" className="space-y-3 rounded-xl border border-line bg-surface p-4">
        {[0, 1, 2, 3, 4].map((row) => (
          <Skeleton key={row} className="h-11 w-full" />
        ))}
      </div>
    )
  }

  if (rows.length === 0) return empty ?? null

  return (
    <>
      <div className="hidden overflow-hidden rounded-xl border border-line bg-surface sm:block">
        <table className="w-full border-collapse">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr className="border-b border-line bg-sunken">
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={`px-4 py-3 text-start text-sm font-semibold text-ink ${column.className ?? ''}`}
                >
                  {column.sort && onSort ? (
                    <SortButton column={column} sort={sort} order={order} onSort={onSort} />
                  ) : (
                    column.header
                  )}
                </th>
              ))}
              {actions ? (
                <th scope="col" className="px-4 py-3 text-end text-sm font-semibold text-ink">
                  Actions
                </th>
              ) : null}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={rowKey(row)} className="border-b border-line last:border-0">
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={`px-4 py-3 align-middle text-[15px] leading-6 text-ink ${column.className ?? ''}`}
                  >
                    {column.cell(row)}
                  </td>
                ))}
                {actions ? <td className="px-4 py-3 text-end">{actions(row)}</td> : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ul className="space-y-3 sm:hidden">
        {rows.map((row) => (
          <li key={rowKey(row)} className="rounded-xl border border-line bg-surface p-4">
            <div className="flex items-start justify-between gap-3">
              <p className="text-[17px] leading-6 font-semibold text-ink">{cardTitle(row)}</p>
              {actions ? actions(row) : null}
            </div>
            <dl className="mt-3 space-y-2">
              {columns
                .filter((column) => !column.primary)
                .map((column) => (
                  <div key={column.key} className="flex flex-wrap items-center gap-x-2">
                    <dt className="text-sm text-muted">{column.header}</dt>
                    <dd className="text-[15px] leading-6 text-ink">{column.cell(row)}</dd>
                  </div>
                ))}
            </dl>
          </li>
        ))}
      </ul>
    </>
  )
}
