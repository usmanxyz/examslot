import { formatCnic, formatDate, formatPhone, formatScore, titleCase } from '../../lib/format'

function groups(me) {
  return [
    {
      title: 'Personal',
      items: [
        { term: 'Full name', value: me.full_name },
        { term: 'Email', value: me.email },
        { term: 'Mobile', value: formatPhone(me.phone) },
        { term: 'CNIC or B-Form', value: formatCnic(me.cnic) },
        { term: 'Date of birth', value: formatDate(`${me.date_of_birth}T00:00:00+05:00`) },
        { term: 'Gender', value: titleCase(me.gender) },
        { term: 'Address', value: me.address },
      ],
    },
    {
      title: 'Guardian',
      items: [
        { term: 'Name', value: me.guardian_name },
        { term: 'CNIC', value: formatCnic(me.guardian_cnic) },
        { term: 'Occupation', value: me.guardian_occupation },
        { term: 'Mobile', value: formatPhone(me.guardian_phone) },
        { term: 'Emergency number', value: formatPhone(me.emergency_phone) },
      ],
    },
    {
      title: 'Academic',
      items: [
        { term: 'Registration number', value: me.registration_no },
        { term: 'Program', value: me.program },
        { term: 'Semester', value: String(me.semester) },
        { term: 'Session', value: me.session },
        { term: 'Previous qualification', value: me.previous_qualification },
        { term: 'Previous institute', value: me.previous_institute },
        { term: 'Previous score', value: formatScore(me.previous_score_type, me.previous_score) },
        { term: 'Exam branch', value: me.branch ? `${me.branch.name}, ${me.branch.city}` : 'Not chosen yet' },
      ],
    },
  ]
}

export default function StudentRecord({ me }) {
  return (
    <div className="grid grid-cols-1 items-start gap-4 pt-4 lg:grid-cols-3">
      {groups(me).map((group) => (
        <section key={group.title} className="overflow-hidden rounded-xl border border-line bg-surface">
          <h3 className="border-b border-line bg-sunken px-4 py-2.5 text-[15px] leading-6 font-semibold text-ink">
            {group.title}
          </h3>
          <dl className="divide-y divide-line">
            {group.items.map((item) => (
              <div
                key={item.term}
                className="grid grid-cols-1 gap-x-4 px-4 py-2.5 sm:grid-cols-[minmax(0,11rem)_minmax(0,1fr)] lg:grid-cols-1"
              >
                <dt className="text-sm leading-6 text-muted">{item.term}</dt>
                <dd className="tabular text-[15px] leading-6 break-words text-ink">{item.value}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </div>
  )
}
