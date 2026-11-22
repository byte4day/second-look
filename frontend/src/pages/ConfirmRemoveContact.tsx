import { useMutation } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { strings } from '../strings.ts'

export function ConfirmRemoveContact() {
  const { contactId = '' } = useParams()
  const navigate = useNavigate()

  const remove = useMutation({
    mutationFn: () => api.removeFamily(Number(contactId)),
    onSuccess: () => navigate('/family'),
  })

  return (
    <div className="page-column">
      <h1>{strings.confirmRemoveTitle}</h1>
      <p>{strings.confirmRemoveBody}</p>
      <Button
        variant="danger"
        block
        disabled={remove.isPending}
        onClick={() => remove.mutate()}
      >
        {strings.confirmRemoveYes}
      </Button>
      <Button variant="secondary" block onClick={() => navigate('/family')}>
        {strings.confirmRemoveNo}
      </Button>
    </div>
  )
}