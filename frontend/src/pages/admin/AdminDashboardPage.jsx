import { Link } from 'react-router'

import PageHeader from '../../components/ui/PageHeader'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

const CARDS = [
  { to: '/admin/students', title: 'Students', body: 'Search student records and page through the list.' },
  { to: '/admin/requests', title: 'Requests', body: 'Approve or reject pending change requests.' },
]

export default function AdminDashboardPage() {
  useDocumentTitle('Dashboard')

  return (
    <div className="space-y-8">
      <PageHeader title="Dashboard" meta="Manage students and change requests." />
      <div className="grid gap-4 sm:grid-cols-2">
        {CARDS.map((card) => (
          <Link
            key={card.to}
            to={card.to}
            className="rounded-xl border border-line bg-surface p-5 transition-colors duration-120 hover:bg-sunken"
          >
            <span className="block text-[17px] leading-6 font-semibold text-primary">{card.title}</span>
            <span className="mt-1 block text-base text-muted">{card.body}</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
