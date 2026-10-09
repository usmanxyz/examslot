import { useDocumentTitle } from '../../hooks/useDocumentTitle'

export function Section({ heading, children }) {
  return (
    <section className="space-y-3">
      <h2 className="font-serif text-[22px] leading-7 font-semibold tracking-[-0.01em] text-ink">{heading}</h2>
      {children}
    </section>
  )
}

export function Paragraph({ children }) {
  return <p className="text-base leading-7 text-muted">{children}</p>
}

export function List({ items }) {
  return (
    <ul className="list-disc space-y-2 ps-5 text-base leading-7 text-muted">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  )
}

export function Table({ columns, rows }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line">
      <table className="w-full border-collapse text-start text-[15px] leading-6">
        <thead>
          <tr className="bg-sunken">
            {columns.map((column) => (
              <th key={column} scope="col" className="px-4 py-3 text-start font-semibold text-ink">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[0]} className="border-t border-line align-top">
              {row.map((cell, index) => (
                <td key={columns[index] ?? index} className="px-4 py-3 text-muted">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function LegalPage({ title, updated, intro, children }) {
  useDocumentTitle(title)

  return (
    <article className="mx-auto w-full max-w-[44rem] pt-10 pb-16">
      <h1 className="font-serif text-[28px] leading-9 font-semibold tracking-[-0.01em] sm:text-[34px] sm:leading-[42px]">
        {title}
      </h1>
      {updated ? <p className="mt-2 text-sm text-muted">Last updated {updated}</p> : null}
      {intro ? <p className="mt-6 text-[17px] leading-7 text-ink">{intro}</p> : null}
      <div className="mt-8 space-y-8">{children}</div>
    </article>
  )
}
