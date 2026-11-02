import { describe, expect, it, vi } from 'vitest'
import { ApiProblem, networkProblem } from '~/api/problems'
import { CONFLICT, type PendingStore, SaveQueue, type SaveStatus } from '~/features/editor/utils/save-queue'

type Payload = { text: string }

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (error: unknown) => void
  const promise = new Promise<T>((ok, fail) => {
    resolve = ok
    reject = fail
  })
  return { promise, resolve, reject }
}

function memoryStore(initial: Record<string, Payload> = {}): PendingStore<Payload> & { saved: Record<string, Payload> } {
  const store = {
    saved: { ...initial },
    load: () => ({ ...store.saved }),
    save: (pending: Record<string, Payload>) => {
      store.saved = pending
    },
  }
  return store
}

const flush = () => new Promise(resolve => setTimeout(resolve, 0))

describe('SaveQueue', () => {
  it('sends saves one at a time, each on the previous revision', async () => {
    const send = vi.fn((_p: Payload, revision: number) => Promise.resolve({ revision: revision + 1 }))
    const queue = new SaveQueue<Payload>({ revision: 1, send })

    queue.save('q1', { text: 'a' })
    queue.save('q2', { text: 'b' })
    await flush()

    expect(send.mock.calls.map(call => call[1])).toEqual([1, 2])
    expect(queue.status).toBe('saved')
    expect(queue.revision).toBe(3)
  })

  it('a newer save of the same key replaces one still waiting', async () => {
    const first = deferred<{ revision: number }>()
    const send = vi.fn().mockReturnValueOnce(first.promise).mockResolvedValue({ revision: 3 })
    const queue = new SaveQueue<Payload>({ revision: 1, send })

    queue.save('q1', { text: 'a' })
    queue.save('q2', { text: 'b' })
    queue.save('q2', { text: 'bb' })
    first.resolve({ revision: 2 })
    await flush()

    expect(send.mock.calls.map(call => call[0])).toEqual([{ text: 'a' }, { text: 'bb' }])
  })

  it('typing during a save sends the newer text afterwards', async () => {
    const first = deferred<{ revision: number }>()
    const send = vi.fn().mockReturnValueOnce(first.promise).mockResolvedValue({ revision: 3 })
    const queue = new SaveQueue<Payload>({ revision: 1, send })

    queue.save('q1', { text: 'a' })
    queue.save('q1', { text: 'ab' })
    first.resolve({ revision: 2 })
    await flush()

    expect(send.mock.calls.map(call => call[0])).toEqual([{ text: 'a' }, { text: 'ab' }])
    expect(queue.isPending('q1')).toBe(false)
  })

  it('retries while offline and says so', async () => {
    const statuses: SaveStatus[] = []
    const send = vi.fn().mockRejectedValueOnce(networkProblem()).mockResolvedValue({ revision: 2 })
    const wait = vi.fn(() => Promise.resolve())
    const queue = new SaveQueue<Payload>({ revision: 1, send, wait, onStatus: s => statuses.push(s) })

    queue.save('q1', { text: 'a' })
    await flush()

    expect(send).toHaveBeenCalledTimes(2)
    expect(wait).toHaveBeenCalledWith(1000)
    expect(statuses).toContain('offline')
    expect(queue.status).toBe('saved')
  })

  it('stops at a conflict and keeps the unsaved text', async () => {
    const store = memoryStore()
    const send = vi.fn().mockRejectedValue(new ApiProblem({ status: 409, code: CONFLICT, detail: 'x' }))
    const queue = new SaveQueue<Payload>({ revision: 1, send, store })

    queue.save('q1', { text: 'mine' })
    queue.save('q2', { text: 'too' })
    await flush()

    expect(send).toHaveBeenCalledTimes(1)
    expect(queue.status).toBe('conflict')
    expect(store.saved).toEqual({ q1: { text: 'mine' }, q2: { text: 'too' } })
  })

  it('a refused save is reported, dropped, and the rest go on', async () => {
    const onFailed = vi.fn()
    const refused = new ApiProblem({ status: 422, code: 'validation_error', detail: 'x' })
    const send = vi.fn().mockRejectedValueOnce(refused).mockResolvedValue({ revision: 2 })
    const queue = new SaveQueue<Payload>({ revision: 1, send, onFailed })

    queue.save('q1', { text: 'bad' })
    await flush()
    expect(queue.status).toBe('failed')
    queue.save('q2', { text: 'good' })
    await flush()

    expect(onFailed).toHaveBeenCalledWith('q1', refused)
    expect(queue.status).toBe('saved')
  })

  it('saves waiting in storage are sent after a reload', async () => {
    const store = memoryStore({ q1: { text: 'before refresh' } })
    const send = vi.fn().mockResolvedValue({ revision: 5 })

    const queue = new SaveQueue<Payload>({ revision: 4, send, store })
    await flush()

    expect(send).toHaveBeenCalledWith({ text: 'before refresh' }, 4)
    expect(queue.revision).toBe(5)
    expect(store.saved).toEqual({})
  })

  it('tasks wait their turn and share the revision chain', async () => {
    const send = vi.fn((_p: Payload, revision: number) => Promise.resolve({ revision: revision + 1 }))
    const queue = new SaveQueue<Payload>({ revision: 1, send })

    queue.save('q1', { text: 'a' })
    const result = await queue.run(revision => Promise.resolve({ revision: revision + 1, made: revision }))

    expect(result).toEqual({ revision: 3, made: 2 })
    expect(queue.revision).toBe(3)
  })

  it('a failed task rejects without stopping the queue, unless it is a conflict', async () => {
    const send = vi.fn().mockResolvedValue({ revision: 2 })
    const queue = new SaveQueue<Payload>({ revision: 1, send })

    await expect(queue.run(() => Promise.reject(networkProblem()))).rejects.toMatchObject({ code: 'network_error' })
    expect(queue.status).toBe('saved')
    await expect(queue.run(() => Promise.reject(new ApiProblem({ status: 409, code: CONFLICT, detail: 'x' })))).rejects.toBeInstanceOf(ApiProblem)
    expect(queue.status).toBe('conflict')
  })
})
