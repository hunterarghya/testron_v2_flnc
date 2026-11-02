// Retry requests that are safe to repeat when the network drops (frontend_spec.md §3).
// POSTs are never repeated here: the server might already have done the work.
import { networkProblem } from '~/api/problems'

const REPEATABLE_METHODS = new Set(['GET', 'PUT'])
const RETRY_DELAYS_MS = [300, 1000]

export type FetchFn = (request: Request) => Promise<Response>
export type WaitFn = (ms: number) => Promise<void>

const wait: WaitFn = ms => new Promise(resolve => setTimeout(resolve, ms))

export function createRetryingFetch(baseFetch: FetchFn = request => fetch(request), pause: WaitFn = wait): FetchFn {
  return async (request) => {
    const delays = REPEATABLE_METHODS.has(request.method) ? RETRY_DELAYS_MS : []
    for (const delay of [...delays, null]) {
      try {
        // A body can be read only once, so every try sends a fresh copy
        return await baseFetch(request.clone())
      }
      catch (error) {
        if (isAbort(error)) {
          throw error
        }
        if (delay === null) {
          throw networkProblem()
        }
        await pause(delay)
      }
    }
    throw networkProblem()
  }
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}
