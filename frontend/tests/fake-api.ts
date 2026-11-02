// A stand-in for `~/api/client` in tests: each method is a spy whose answers the test sets.
// Use with `vi.mock('~/api/client', () => fakeClientModule(fake))`.
import { vi } from 'vitest'
import { ApiProblem } from '~/api/problems'

type Answer = { data?: unknown, response: Response }

export function fakeApi() {
  return {
    GET: vi.fn<(path: string, init?: unknown) => Promise<Answer>>(),
    POST: vi.fn<(path: string, init?: unknown) => Promise<Answer>>(),
    PATCH: vi.fn<(path: string, init?: unknown) => Promise<Answer>>(),
    DELETE: vi.fn<(path: string, init?: unknown) => Promise<Answer>>(),
  }
}

export type FakeApi = ReturnType<typeof fakeApi>

export function ok(data?: unknown): Promise<Answer> {
  return Promise.resolve({ data, response: new Response(null, { status: data === undefined ? 204 : 200 }) })
}

export function fails(status: number, code: string): Promise<never> {
  return Promise.reject(new ApiProblem({ status, code, detail: code }))
}

export function fakeClientModule(api: FakeApi) {
  return {
    api,
    unwrap: async (pending: Promise<Answer>) => (await pending).data,
  }
}
