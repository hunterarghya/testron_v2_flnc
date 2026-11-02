// Who is logged in, loaded once per app load and shared by every page (frontend_spec.md §1).
// Later redirects use the cached value; "Check again" and login refresh it.
import { useState } from '#imports'
import { api, unwrap } from '~/api/client'
import type { SessionUser } from '~/api/types'

export function useSession() {
  const user = useState<SessionUser | null>('session-user', () => null)
  const loaded = useState<boolean>('session-loaded', () => false)

  /** Ask the server again. Also sets the CSRF cookie that every later write needs. */
  async function load(): Promise<SessionUser | null> {
    await api.GET('/api/v1/auth/csrf')
    const session = await unwrap(api.GET('/api/v1/auth/session'))
    user.value = session.user
    loaded.value = true
    return session.user
  }

  function set(next: SessionUser | null): void {
    user.value = next
    loaded.value = true
  }

  async function logOut(): Promise<void> {
    await api.POST('/api/v1/auth/logout')
    set(null)
  }

  return { user, loaded, load, set, logOut }
}
