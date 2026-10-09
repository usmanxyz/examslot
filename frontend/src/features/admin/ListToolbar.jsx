import Button from '../../components/ui/Button'
import FilterSelect from '../../components/ui/FilterSelect'
import SearchInput from '../../components/ui/SearchInput'

export default function ListToolbar({ search, filters = [], activeFilterCount, onClear }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {search ? (
        <SearchInput
          id="list-search"
          label={search.label}
          placeholder={search.placeholder}
          value={search.value}
          onChange={search.onChange}
        />
      ) : null}
      {filters.map((filter) => (
        <FilterSelect
          key={filter.id}
          id={filter.id}
          label={filter.label}
          allLabel={filter.allLabel}
          value={filter.value}
          onChange={filter.onChange}
          options={filter.options}
        />
      ))}
      {activeFilterCount > 0 ? (
        <Button variant="tertiary" size="sm" onClick={onClear}>
          Clear filters ({activeFilterCount})
        </Button>
      ) : null}
    </div>
  )
}
