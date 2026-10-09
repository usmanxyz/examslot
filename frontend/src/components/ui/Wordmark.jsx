export default function Wordmark() {
  return (
    <span className="inline-flex items-center gap-2 text-primary" role="img" aria-label="ExamSlot">
      <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
        <rect
          x="1.5"
          y="3.5"
          width="17"
          height="13"
          rx="4"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
        />
        <rect x="4.5" y="11" width="11" height="2.5" rx="1.25" fill="currentColor" />
      </svg>
      <span className="font-serif text-2xl font-semibold tracking-tight text-ink">ExamSlot</span>
    </span>
  )
}
