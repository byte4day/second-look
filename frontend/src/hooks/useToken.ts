import { useSyncExternalStore } from 'react'
import { getToken, subscribeToken } from '../api/client.ts'

/** The saved sign-in token, re-rendering whenever it is set, cleared or expires. */
export function useToken(): string | null {
  return useSyncExternalStore(subscribeToken, getToken, () => null)
}
