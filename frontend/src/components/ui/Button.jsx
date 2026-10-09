import Spinner from './Spinner'

const VARIANTS = {
  primary: 'bg-primary text-on-primary hover:bg-primary-hover border border-transparent',
  secondary: 'bg-surface text-ink border border-control hover:bg-sunken',
  tertiary: 'bg-transparent text-primary border border-transparent hover:bg-primary-soft',
  danger: 'bg-danger text-on-danger border border-transparent hover:opacity-90',
  dangerOutline: 'bg-surface text-danger border border-danger hover:bg-danger-soft',
}

const SIZES = {
  md: 'min-h-11 px-4 text-base',
  sm: 'min-h-9 px-3 text-sm',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  pending = false,
  pendingLabel,
  type = 'button',
  className = '',
  children,
  disabled,
  ...rest
}) {
  return (
    <button
      type={type}
      disabled={disabled || pending}
      aria-busy={pending || undefined}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors duration-120 disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...rest}
    >
      {pending ? <Spinner /> : null}
      <span>{pending && pendingLabel ? pendingLabel : children}</span>
    </button>
  )
}
