import { useNavigate } from 'react-router'

import Button from '../../components/ui/Button'
import ErrorState from '../../components/ui/ErrorState'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

export default function NotFoundPage() {
  useDocumentTitle('Page not found')
  const navigate = useNavigate()

  return (
    <div className="mx-auto max-w-[44rem] py-10 sm:py-14">
      <ErrorState variant="notFound">
        <Button variant="secondary" onClick={() => navigate('/login')}>
          Go to sign in
        </Button>
      </ErrorState>
    </div>
  )
}
