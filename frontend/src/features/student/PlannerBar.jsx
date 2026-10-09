import Button from '../../components/ui/Button'

export default function PlannerBar({ progress, complete, onReview }) {
  return (
    <div className="print-hidden fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] lg:hidden">
      <div className="mx-auto flex min-h-14 max-w-[72rem] items-center justify-between gap-4 px-4">
        <p aria-live="polite" className="tabular text-sm font-medium text-ink">
          {progress}
        </p>
        <Button size="sm" disabled={!complete} onClick={onReview}>
          Review
        </Button>
      </div>
    </div>
  )
}
