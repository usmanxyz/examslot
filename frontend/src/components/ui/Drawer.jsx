import Dialog from './Dialog'

export default function Drawer({ open, onClose, title, children }) {
  return (
    <Dialog open={open} onClose={onClose} title={title} placement="drawer">
      {children}
    </Dialog>
  )
}
