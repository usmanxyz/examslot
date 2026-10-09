import { ChevronFirst, ChevronLast, ChevronLeft, ChevronRight } from 'lucide-react'

import IconButton from './IconButton'
import Select from './Select'

function pageNumbers(page, totalPages) {
  return [page - 1, page, page + 1].filter((value) => value >= 1 && value <= totalPages)
}

export default function Pagination({ page, pageSize, pageSizes, total, totalPages, onPageChange, onPageSizeChange }) {
  const pages = Math.max(1, totalPages)
  const first = total === 0 ? 0 : (page - 1) * pageSize + 1
  const last = Math.min(page * pageSize, total)

  return (
    <div className="flex flex-wrap items-center justify-between gap-4">
      <p role="status" className="tabular text-sm text-muted">
        Showing {first} to {last} of {total}
      </p>
      <div className="flex flex-wrap items-center gap-3">
        <div className="w-[7.5rem]">
          <label htmlFor="page-size" className="sr-only">
            Rows per page
          </label>
          <Select
            id="page-size"
            value={String(pageSize)}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
            options={pageSizes.map((size) => ({ value: String(size), label: `${size} rows` }))}
          />
        </div>
        <nav aria-label="Pagination" className="flex items-center gap-1">
          <IconButton
            label="First page"
            icon={ChevronFirst}
            disabled={page <= 1}
            className="disabled:opacity-40"
            onClick={() => onPageChange(1)}
          />
          <IconButton
            label="Previous page"
            icon={ChevronLeft}
            disabled={page <= 1}
            className="disabled:opacity-40"
            onClick={() => onPageChange(page - 1)}
          />
          {pageNumbers(page, pages).map((value) => (
            <button
              key={value}
              type="button"
              aria-current={value === page ? 'page' : undefined}
              onClick={() => onPageChange(value)}
              className={`tabular inline-flex size-11 items-center justify-center rounded-lg text-base ${
                value === page ? 'bg-primary text-on-primary' : 'text-ink hover:bg-sunken'
              }`}
            >
              {value}
            </button>
          ))}
          <IconButton
            label="Next page"
            icon={ChevronRight}
            disabled={page >= pages}
            className="disabled:opacity-40"
            onClick={() => onPageChange(page + 1)}
          />
          <IconButton
            label="Last page"
            icon={ChevronLast}
            disabled={page >= pages}
            className="disabled:opacity-40"
            onClick={() => onPageChange(pages)}
          />
        </nav>
      </div>
    </div>
  )
}
