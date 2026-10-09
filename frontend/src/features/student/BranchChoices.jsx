import RadioCard from '../../components/ui/RadioCard'
import { formatPhone } from '../../lib/format'

export default function BranchChoices({ items, selectedId, onSelect }) {
  return (
    <fieldset>
      <legend className="sr-only">Exam branch</legend>
      <div className="space-y-3">
        {items.map((branch) => (
          <RadioCard
            key={branch.id}
            id={`branch-${branch.id}`}
            name="branch"
            value={branch.id}
            checked={selectedId === branch.id}
            onChange={() => onSelect(branch.id)}
            title={branch.name}
            description={`${branch.city} · ${branch.address}`}
            meta={formatPhone(branch.contact_phone)}
            unavailableReason={branch.eligible ? null : branch.reason}
          />
        ))}
      </div>
    </fieldset>
  )
}
