export default function IconButton({ label, icon: Icon, className = '', ...rest }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={`inline-flex size-11 items-center justify-center rounded-lg text-ink transition-colors duration-120 hover:bg-sunken ${className}`}
      {...rest}
    >
      <Icon size={20} strokeWidth={1.75} aria-hidden="true" />
    </button>
  )
}
