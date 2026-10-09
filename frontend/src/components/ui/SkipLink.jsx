export default function SkipLink() {
  return (
    <a
      href="#content"
      className="sr-only rounded-lg bg-surface px-4 py-3 text-primary focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:border focus:border-primary"
    >
      Skip to content
    </a>
  )
}
