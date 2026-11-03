import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  backoffMs,
  createSaveQueue,
  DEBOUNCE_MS,
  MAX_BACKOFF_MS,
  type PendingSave,
  type QueueSnapshot,
  type SaveQueueDeps,
  type SendOutcome,
} from '~/engine/save-queue'

type Answer = string

interface Sent {
  questionId: string
  save: PendingSave<Answer>
  reply: (outcome: SendOutcome) => Promise<void>
}

// A network we answer by hand, and a localStorage stand-in
function harness(stored: QueueSnapshot<Answer> | null = null, serverSeq = 0) {
  const sent: Sent[] = []
  let saved: QueueSnapshot<Answer> | null = stored
  const deps: SaveQueueDeps<Answer> = {
    send: (questionId, save) => new Promise<SendOutcome>((resolve) => {
      sent.push({ questionId, save, reply: async (outcome) => {
        resolve(outcome)
        await vi.advanceTimersByTimeAsync(0)
      } })
    }),
    storage: {
      read: () => saved,
      write: (snapshot) => {
        saved = structuredClone(snapshot)
      },
      clear: () => {
        saved = null
      },
    },
    onStop: vi.fn(),
    onChange: vi.fn(),
    onDropped: vi.fn(),
    random: () => 0.5,
  }
  const queue = createSaveQueue(deps, serverSeq)
  return { queue, deps, sent, stored: () => saved }
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('save queue (frontend_spec.md §5.2)', () => {
  it('sends a choice at once and forgets it once acknowledged', async () => {
    const { queue, sent, stored } = harness()

    queue.change('q1', 'B', false)

    expect(sent.map(s => [s.questionId, s.save])).toEqual([['q1', { answer: 'B', marked_for_review: false, client_seq: 1 }]])
    expect(stored()?.pending.q1?.client_seq).toBe(1)
    expect(queue.waiting()).toBe(1)
    await sent[0]!.reply('saved')
    expect(queue.waiting()).toBe(0)
    expect(stored()).toEqual({ seq: 1, pending: {} })
  })

  it('waits for numeric typing to pause', async () => {
    const { queue, sent } = harness()

    queue.change('q3', '4', false, { debounce: true })
    queue.change('q3', '46', false, { debounce: true })
    expect(sent).toHaveLength(0)
    await vi.advanceTimersByTimeAsync(DEBOUNCE_MS)

    expect(sent.map(s => s.save.answer)).toEqual(['46'])
  })

  it('keeps a newer change made while the older one was on its way', async () => {
    const { queue, sent } = harness()

    queue.change('q1', 'A', false)
    queue.change('q1', 'C', true)
    await sent[0]!.reply('saved')

    expect(sent.map(s => s.save)).toEqual([
      { answer: 'A', marked_for_review: false, client_seq: 1 },
      { answer: 'C', marked_for_review: true, client_seq: 2 },
    ])
    expect(queue.waiting()).toBe(1)
  })

  it('sends at most two at a time', async () => {
    const { queue, sent } = harness()

    for (const q of ['q1', 'q2', 'q3']) queue.change(q, 'A', false)
    expect(sent.map(s => s.questionId)).toEqual(['q1', 'q2'])
    await sent[0]!.reply('saved')

    expect(sent.map(s => s.questionId)).toEqual(['q1', 'q2', 'q3'])
  })

  it('offline: keeps the answer and tries again with growing pauses', async () => {
    const { queue, sent } = harness()

    queue.change('q1', 'A', false)
    await sent[0]!.reply('retry')
    expect(queue.offline()).toBe(true)
    await vi.advanceTimersByTimeAsync(999)
    expect(sent).toHaveLength(1)
    await vi.advanceTimersByTimeAsync(1)
    await sent[1]!.reply('retry')
    await vi.advanceTimersByTimeAsync(2000)
    await sent[2]!.reply('saved')

    expect(queue.offline()).toBe(false)
    expect(queue.waiting()).toBe(0)
  })

  it('pauses double up to 15 s, spread a little', () => {
    expect([1, 2, 3, 4, 5, 9].map(n => backoffMs(n, 0.5))).toEqual([1000, 2000, 4000, 8000, 15000, MAX_BACKOFF_MS])
    expect(backoffMs(1, 0)).toBe(800)
    expect(backoffMs(0, 1)).toBe(1200)
  })

  it('drops an answer whose stage has closed', async () => {
    const { queue, deps, sent } = harness()

    queue.change('q1', 'A', false)
    await sent[0]!.reply('drop')

    expect(deps.onDropped).toHaveBeenCalledWith('q1')
    expect(queue.waiting()).toBe(0)
  })

  it.each(['ended', 'taken_over'] as const)('stops and clears the device copy when %s', async (reason) => {
    const { queue, deps, sent, stored } = harness()

    queue.change('q1', 'A', false)
    queue.change('q2', 'B', false)
    await sent[0]!.reply(reason)
    await sent[1]!.reply('saved')
    queue.change('q3', 'C', false)
    queue.flush()

    expect(deps.onStop).toHaveBeenCalledExactlyOnceWith(reason)
    expect(stored()).toBeNull()
    expect(sent).toHaveLength(2)
  })

  it('after a reload, resends what was waiting above the server\'s seq', () => {
    const left = { seq: 4, pending: { q2: { answer: 'D', marked_for_review: false, client_seq: 4 } } }
    const { queue, sent } = harness(left, 9)

    queue.change('q1', 'A', false)

    expect(sent.map(s => [s.questionId, s.save.client_seq])).toEqual([['q2', 4], ['q1', 10]])
    expect(queue.lastSeq()).toBe(10)
  })

  it('drain resolves when everything is sent, or gives up after the timeout', async () => {
    const empty = harness()
    await expect(empty.queue.drain(100)).resolves.toBe(true)

    const { queue, sent } = harness()
    queue.change('q1', 'A', false, { debounce: true })
    const draining = queue.drain(10_000)
    await sent[0]!.reply('saved')
    await expect(draining).resolves.toBe(true)

    queue.change('q2', 'B', false)
    const stuck = queue.drain(100)
    await vi.advanceTimersByTimeAsync(100)
    await expect(stuck).resolves.toBe(false)
  })

  it('a stopped queue takes no changes and a late reply is ignored', async () => {
    const { queue, sent, deps } = harness()
    queue.change('q1', 'A', false)
    queue.stop()

    queue.change('q2', 'B', false)
    await sent[0]!.reply('saved')

    expect(sent).toHaveLength(1)
    expect(deps.onDropped).not.toHaveBeenCalled()
  })

  it('uses Math.random when no source is given', () => {
    const { deps } = harness()
    const queue = createSaveQueue({ ...deps, random: undefined }, 0)
    expect(queue.waiting()).toBe(0)
  })
})
