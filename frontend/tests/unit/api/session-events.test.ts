import { describe, expect, it, vi } from 'vitest'
import { createApiClient } from '~/api/client'
import { notifySessionExpired, onSessionExpired } from '~/api/session-events'

function clientAnswering(status: number, code: string) {
  return createApiClient({
    baseUrl: 'http://app.test',
    fetch: async () => Response.json({ code, detail: 'x' }, { status }),
    readCookies: () => '',
  })
}

describe('session expired', () => {
  it('tells every listener until they unsubscribe', () => {
    const listener = vi.fn()
    const unsubscribe = onSessionExpired(listener)

    notifySessionExpired()
    unsubscribe()
    notifySessionExpired()

    expect(listener).toHaveBeenCalledTimes(1)
  })

  it('is raised by any 401 not_authenticated answer', async () => {
    const listener = vi.fn()
    const unsubscribe = onSessionExpired(listener)

    await clientAnswering(401, 'not_authenticated').GET('/api/v1/auth/session').catch(() => {})
    unsubscribe()

    expect(listener).toHaveBeenCalledTimes(1)
  })

  it('is not raised by a failed login', async () => {
    const listener = vi.fn()
    const unsubscribe = onSessionExpired(listener)

    await clientAnswering(401, 'invalid_credentials').GET('/api/v1/auth/session').catch(() => {})
    unsubscribe()

    expect(listener).not.toHaveBeenCalled()
  })
})
