import { useMutation } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { api } from '../api/client.ts'
import { Button } from '../components/Button.tsx'
import { strings } from '../strings.ts'

export function AcceptInvitation() {
  const { token = '' } = useParams()

  const accept = useMutation({
    mutationFn: () => api.acceptInvitation(token),
  })

  return (
    <div className="page-column">
      <h1>{strings.inviteTitle}</h1>
      <p>{strings.inviteBody}</p>
      {accept.isSuccess ? (
        <p role="status">{strings.inviteDone}</p>
      ) : (
        <Button
          variant="primary"
          block
          disabled={!token || accept.isPending}
          onClick={() => accept.mutate()}
        >
          {strings.inviteAccept}
        </Button>
      )}
    </div>
  )
}