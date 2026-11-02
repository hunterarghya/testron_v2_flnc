import { describe, expect, it } from 'vitest'
import { NETWORK_ERROR } from '~/api/problems'
import { createRetryingFetch, type FetchFn } from '~/api/retry'

function flakyFetch(failures: number) {
  let calls = 0
  const fetchFn: FetchFn = async () => {
    calls += 1
    if (calls <= failures) {
      throw new TypeError('Failed to fetch')
    }
    return new Response('ok')
  }
  return { fetchFn, calls: () => calls }
}

function retrying(fetchFn: FetchFn) {
  const waits: number[] = []
  const retry = createRetryingFetch(fetchFn, async (ms) => {
    waits.push(ms)
  })
  return { retry, waits }
}

describe('retrying fetch', () => {
  it('retries a GET twice with growing waits', async () => {
    const flaky = flakyFetch(2)
    const { retry, waits } = retrying(flaky.fetchFn)

    const response = await retry(new Request('http://app.test/x'))

    expect(await response.text()).toBe('ok')
    expect(flaky.calls()).toBe(3)
    expect(waits).toEqual([300, 1000])
  })

  it('gives up after two retries with a network problem', async () => {
    const { retry } = retrying(flakyFetch(3).fetchFn)

    await expect(retry(new Request('http://app.test/x'))).rejects.toMatchObject({
      code: NETWORK_ERROR,
      status: 0,
    })
  })

  it('retries a PUT, whose repeat is harmless', async () => {
    const flaky = flakyFetch(1)
    const { retry } = retrying(flaky.fetchFn)

    await retry(new Request('http://app.test/x', { method: 'PUT', body: '{}' }))

    expect(flaky.calls()).toBe(2)
  })

  it('never repeats a POST', async () => {
    const flaky = flakyFetch(1)
    const { retry } = retrying(flaky.fetchFn)

    await expect(retry(new Request('http://app.test/x', { method: 'POST', body: '{}' })))
      .rejects.toMatchObject({ code: NETWORK_ERROR })
    expect(flaky.calls()).toBe(1)
  })

  it('lets a cancelled request stay cancelled', async () => {
    const abort = new DOMException('Aborted', 'AbortError')
    const { retry, waits } = retrying(async () => {
      throw abort
    })

    await expect(retry(new Request('http://app.test/x'))).rejects.toBe(abort)
    expect(waits).toEqual([])
  })
})
