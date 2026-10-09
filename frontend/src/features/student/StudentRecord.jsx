import DefinitionList from '../../components/ui/DefinitionList'
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
    <div className="grid grid-cols-1 gap-8 pt-4 lg:grid-cols-3">
      {groups(me).map((group) => (
        <div key={group.title} className="space-y-3">
          <h3 className="text-[17px] leading-6 font-semibold text-ink">{group.title}</h3>
          <DefinitionList items={group.items} />
        </div>
      ))}
    </div>
  )
}
