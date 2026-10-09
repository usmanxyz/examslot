export default function Skeleton({ className = 'h-4 w-full' }) {
  return <span aria-hidden="true" className={`block rounded-md bg-sunken ${className}`} />
}
