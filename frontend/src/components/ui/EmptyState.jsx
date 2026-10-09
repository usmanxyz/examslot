export default function EmptyState({ title, body, children }) {
  return (
    <div className="rounded-xl border border-line bg-surface px-6 py-10 text-center">
      <p className="text-[17px] leading-6 font-semibold text-ink">{title}</p>
      {body ? <p className="mx-auto mt-2 max-w-[32rem] text-base text-muted">{body}</p> : null}
      {children ? <div className="mt-6 flex justify-center">{children}</div> : null}
    </div>
  )
}
