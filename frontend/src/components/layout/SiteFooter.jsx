import { Link } from 'react-router'

const LINKS = [
  { to: '/about', label: 'About' },
  { to: '/contact', label: 'Contact' },
  { to: '/terms', label: 'Terms' },
  { to: '/privacy', label: 'Privacy' },
  { to: '/disclaimer', label: 'Disclaimer' },
]

export default function SiteFooter() {
  return (
    <footer className="print-hidden pt-8">
      <nav aria-label="Footer" className="border-t border-line">
        <div className="mx-auto flex max-w-[72rem] flex-wrap items-center gap-x-6 gap-y-2 px-4 py-6 text-[13px] leading-[18px] text-muted sm:px-6 lg:px-8">
          {LINKS.map((link) => (
            <Link key={link.to} to={link.to} className="min-h-11 content-center hover:text-primary">
              {link.label}
            </Link>
          ))}
          
        </div>
      </nav>
    </footer>
  )
}
