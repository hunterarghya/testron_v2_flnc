// Django's CSRF check: unsafe requests echo the `csrftoken` cookie in a header
// (architecture.md §5.2).

const COOKIE = 'csrftoken'
const HEADER = 'X-CSRFToken'
const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

export function csrfToken(cookieHeader: string): string | null {
  for (const part of cookieHeader.split(';')) {
    const [name, ...value] = part.trim().split('=')
    if (name === COOKIE) {
      return decodeURIComponent(value.join('='))
    }
  }
  return null
}

export function withCsrf(request: Request, cookieHeader: string): Request {
  const token = csrfToken(cookieHeader)
  if (token && UNSAFE_METHODS.has(request.method)) {
    request.headers.set(HEADER, token)
  }
  return request
}
