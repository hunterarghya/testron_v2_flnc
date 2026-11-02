import { describe, expect, it } from 'vitest'
import { csrfToken, withCsrf } from '~/api/csrf'

const COOKIES = 'sessionid=abc; csrftoken=tok%3D123; theme=light'

describe('csrf', () => {
  it('reads the token from the cookie header', () => {
    expect(csrfToken(COOKIES)).toBe('tok=123')
  })

  it('finds no token when the cookie is missing', () => {
    expect(csrfToken('sessionid=abc')).toBeNull()
    expect(csrfToken('')).toBeNull()
  })

  it.each(['POST', 'PUT', 'PATCH', 'DELETE'])('adds the header to %s', (method) => {
    const request = withCsrf(new Request('http://app.test/x', { method }), COOKIES)

    expect(request.headers.get('X-CSRFToken')).toBe('tok=123')
  })

  it('leaves reads alone', () => {
    const request = withCsrf(new Request('http://app.test/x'), COOKIES)

    expect(request.headers.has('X-CSRFToken')).toBe(false)
  })

  it('sends nothing when there is no token yet', () => {
    const request = withCsrf(new Request('http://app.test/x', { method: 'POST' }), '')

    expect(request.headers.has('X-CSRFToken')).toBe(false)
  })
})
