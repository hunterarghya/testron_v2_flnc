import { describe, expect, it } from 'vitest'
import { createApiClient, unwrap } from '~/api/client'
import { ApiProblem } from '~/api/problems'

const HEALTH = { status: 'ok', server_now: '2026-11-12T04:30:00Z', version: 'dev', commit: 'abc' }

function respondWith(response: Response) {
  const seen: Request[] = []
  const client = createApiClient({
    baseUrl: 'http://app.test',
    fetch: async (request) => {
      seen.push(request)
      return response.clone()
    },
    readCookies: () => 'csrftoken=tok123',
  })
  return { client, seen }
}

function problemResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/problem+json' },
  })
}

describe('api client', () => {
  it('returns the typed body on success', async () => {
    const { client, seen } = respondWith(Response.json(HEALTH))

    const health = await unwrap(client.GET('/api/v1/healthz', { params: { query: { deep: true } } }))

    expect(health).toEqual(HEALTH)
    expect(seen[0]?.url).toBe('http://app.test/api/v1/healthz?deep=true')
  })

  it('throws an ApiProblem built from problem+json', async () => {
    const { client } = respondWith(problemResponse(503, {
      code: 'database_unavailable',
      detail: 'The database is not reachable',
      trace_id: 'trace-1',
      context: { retry: true },
    }))

    const error = await client.GET('/api/v1/healthz').catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(ApiProblem)
    expect(error).toMatchObject({
      status: 503,
      code: 'database_unavailable',
      traceId: 'trace-1',
      context: { retry: true },
    })
  })

  it('keeps field errors from a validation problem', async () => {
    const errors = [{ field: 'deep', code: 'bool_parsing', message: 'Not a boolean' }]
    const { client } = respondWith(problemResponse(422, { code: 'validation_error', errors }))

    await expect(client.GET('/api/v1/healthz')).rejects.toMatchObject({ errors })
  })

  it('treats a non-JSON error page as an internal error with the request id', async () => {
    const { client } = respondWith(new Response('<html>Bad gateway</html>', {
      status: 502,
      statusText: 'Bad Gateway',
      headers: { 'X-Request-ID': 'req-9' },
    }))

    await expect(client.GET('/api/v1/healthz')).rejects.toMatchObject({
      status: 502,
      code: 'internal_error',
      detail: 'Bad Gateway',
      traceId: 'req-9',
    })
  })

  it('does not send the CSRF header on reads', async () => {
    const { client, seen } = respondWith(Response.json(HEALTH))

    await client.GET('/api/v1/healthz')

    expect(seen[0]?.headers.has('X-CSRFToken')).toBe(false)
  })
})
