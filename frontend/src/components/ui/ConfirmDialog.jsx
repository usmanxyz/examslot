import Button from './Button'
import Dialog from './Dialog'

export default function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  body,
  confirmLabel,
  cancelLabel = 'Cancel',
  confirmVariant = 'primary',
  pending = false,
  pendingLabel,
}) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={title}
      description={body}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            {cancelLabel}
          </Button>
          <Button variant={confirmVariant} onClick={onConfirm} pending={pending} pendingLabel={pendingLabel}>
            {confirmLabel}
          </Button>
        </>
      }
    />
  )
}
