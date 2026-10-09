import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'

import TextInput from '../../components/ui/TextInput'

export default function PasswordInput({ className = '', ...rest }) {
  const [visible, setVisible] = useState(false)

  return (
    <div className="relative">
      <TextInput type={visible ? 'text' : 'password'} className={`pe-14 ${className}`} {...rest} />
      <button
        type="button"
        onClick={() => setVisible((current) => !current)}
        aria-pressed={visible}
        className="absolute inset-y-0 end-0 inline-flex min-h-11 items-center gap-1 rounded-e-lg px-3 text-sm font-medium text-primary"
      >
        {visible ? <EyeOff size={18} strokeWidth={1.75} aria-hidden="true" /> : <Eye size={18} strokeWidth={1.75} aria-hidden="true" />}
        {visible ? 'Hide' : 'Show'}
      </button>
    </div>
  )
}
