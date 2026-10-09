export default function Spinner() {
  return (
    <span
      aria-hidden="true"
      className="inline-block size-4 shrink-0 rounded-full border-2 border-current border-t-transparent motion-safe:animate-[spinner_600ms_linear_infinite]"
    />
  )
}
