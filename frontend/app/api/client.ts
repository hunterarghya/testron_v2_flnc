// The only way the app talks to the API (frontend_spec.md §3). Typed end to end by the
// schema generated from docs/api/openapi.json (`just openapi`).
import createClient, { type Client, type Middleware } from 'openapi-fetch'
import { withCsrf } from '~/api/csrf'
import { problemFromResponse } from '~/api/problems'
import { createRetryingFetch, type FetchFn } from '~/api/retry'
import type { paths } from '~/api/schema'

export type ApiClient = Client<paths>

export interface ApiClientOptions {
  // Same origin as the SPA in the browser; tests pass an absolute URL
  baseUrl?: string
  fetch?: FetchFn
  readCookies?: () => string
}

const errorsAsProblems: Middleware = {
  async onResponse({ response }) {
    if (!response.ok) {
      throw await problemFromResponse(response)
    }
    return response
  },
}

function csrfHeader(readCookies: () => string): Middleware {
  return {
    onRequest: ({ request }) => withCsrf(request, readCookies()),
  }
}

export function createApiClient(options: ApiClientOptions = {}): ApiClient {
  const client = createClient<paths>({
    baseUrl: options.baseUrl ?? '',
    fetch: options.fetch ?? createRetryingFetch(),
  })
  const readCookies = options.readCookies ?? (() => document.cookie)
  client.use(csrfHeader(readCookies), errorsAsProblems)
  return client
}

/** The response body. Errors never get here: they are thrown as ApiProblem. */
export async function unwrap<T>(pending: Promise<{ data?: T, response: Response }>): Promise<T> {
  const { data } = await pending
  // Only a 204 has no body, and its type is already "no content"
  return data as T
}

export const api = createApiClient()
