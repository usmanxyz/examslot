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
  confirmDisabled = false,
  pending = false,
  pendingLabel,
  children,
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
          <Button
            variant={confirmVariant}
            onClick={onConfirm}
            disabled={confirmDisabled}
            pending={pending}
            pendingLabel={pendingLabel}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      {children ? <div className="mt-4">{children}</div> : null}
    </Dialog>
  )
}
