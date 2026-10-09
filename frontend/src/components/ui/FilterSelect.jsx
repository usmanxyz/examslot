import Select from './Select'

export default function FilterSelect({ id, label, value, onChange, options, allLabel = 'All' }) {
  return (
    <div className="w-full sm:w-[12rem]">
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <Select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        options={[{ value: '', label: allLabel }, ...options]}
      />
    </div>
  )
}
