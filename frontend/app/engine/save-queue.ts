// Never lose an answer (frontend_spec.md §5.2). Every change gets a higher client_seq and is
// kept on the device (localStorage) until the server acknowledges that exact change. Sends
// go out at most two at a time; a failed one waits and tries again with growing pauses. The
// server keeps only the newest seq per question, so sending again is always safe.

export interface PendingSave<A> {
  answer: A | null
  marked_for_review: boolean
  client_seq: number
}

export interface QueueSnapshot<A> {
  // The last client_seq handed out
  seq: number
  // The newest unsent change per question
  pending: Record<string, PendingSave<A>>
}

// What became of one send: stored; worth trying again (offline, server busy); pointless
// (the question's stage closed); or the attempt is over / owned by another device.
export type SendOutcome = 'saved' | 'retry' | 'drop' | 'ended' | 'taken_over'
export type StopReason = 'ended' | 'taken_over'

export interface QueueStorage<A> {
  read: () => QueueSnapshot<A> | null
  write: (snapshot: QueueSnapshot<A>) => void
  clear: () => void
}

export interface SaveQueueDeps<A> {
  send: (questionId: string, save: PendingSave<A>) => Promise<SendOutcome>
  storage: QueueStorage<A>
  onStop: (reason: StopReason) => void
  // The waiting count or the offline flag changed
  onChange: () => void
  onDropped: (questionId: string) => void
  random?: () => number
}

export interface SaveQueue<A> {
  change: (questionId: string, answer: A | null, markedForReview: boolean, options?: { debounce?: boolean }) => void
  flush: () => void
  // Resolves true once nothing is waiting, false if that takes longer than `timeoutMs`
  drain: (timeoutMs: number) => Promise<boolean>
  waiting: () => number
  offline: () => boolean
  // The next change's seq would be above this
  lastSeq: () => number
  stop: () => void
}

export const MAX_IN_FLIGHT = 2
// Numeric typing waits this long after the last key before saving
export const DEBOUNCE_MS = 500
export const MAX_BACKOFF_MS = 15_000

/** 1 s, 2 s, 4 s … capped at 15 s, each spread by ±20 % so a class doesn't retry in step. */
export function backoffMs(failures: number, random: number): number {
  const base = Math.min(MAX_BACKOFF_MS, 1000 * 2 ** Math.max(0, failures - 1))
  return Math.round(base * (0.8 + 0.4 * random))
}

/** `serverSeq`: the highest client_seq the server holds, so a new device always writes above it. */
export function createSaveQueue<A>(deps: SaveQueueDeps<A>, serverSeq: number): SaveQueue<A> {
  const stored = deps.storage.read()
  const state: QueueSnapshot<A> = {
    seq: Math.max(stored?.seq ?? 0, serverSeq),
    pending: { ...stored?.pending },
  }
  const inFlight = new Set<string>()
  const waiters = new Set<() => void>()
  const random = deps.random ?? Math.random
  let failures = 0
  let stopped = false
  let timer: ReturnType<typeof setTimeout> | undefined

  function waiting(): number {
    return Object.keys(state.pending).length
  }

  function persist(): void {
    deps.storage.write({ seq: state.seq, pending: state.pending })
  }

  function settle(): void {
    deps.onChange()
    if (waiting() === 0 && inFlight.size === 0) {
      waiters.forEach(done => done())
    }
  }

  function wakeIn(ms: number): void {
    clearTimeout(timer)
    timer = setTimeout(flush, ms)
  }

  function forget(questionId: string, sent: PendingSave<A>): void {
    if (state.pending[questionId]?.client_seq === sent.client_seq) {
      state.pending = Object.fromEntries(Object.entries(state.pending).filter(([id]) => id !== questionId))
      persist()
    }
  }

  function stop(): void {
    stopped = true
    clearTimeout(timer)
  }

  function finish(reason: StopReason): void {
    stop()
    state.pending = {}
    deps.storage.clear()
    deps.onStop(reason)
  }

  async function sendOne(questionId: string): Promise<void> {
    const sent = state.pending[questionId]!
    inFlight.add(questionId)
    const outcome = await deps.send(questionId, sent)
    inFlight.delete(questionId)
    if (stopped) return
    if (outcome === 'ended' || outcome === 'taken_over') {
      finish(outcome)
      return
    }
    if (outcome === 'retry') {
      failures += 1
      wakeIn(backoffMs(failures, random()))
      settle()
      return
    }
    failures = 0
    forget(questionId, sent)
    if (outcome === 'drop') deps.onDropped(questionId)
    settle()
    flush()
  }

  function flush(): void {
    if (stopped) return
    for (const questionId of Object.keys(state.pending)) {
      if (inFlight.size >= MAX_IN_FLIGHT) return
      if (!inFlight.has(questionId)) void sendOne(questionId)
    }
  }

  function change(questionId: string, answer: A | null, markedForReview: boolean, options: { debounce?: boolean } = {}): void {
    if (stopped) return
    state.seq += 1
    state.pending[questionId] = { answer, marked_for_review: markedForReview, client_seq: state.seq }
    persist()
    deps.onChange()
    if (options.debounce) wakeIn(DEBOUNCE_MS)
    else flush()
  }

  function drain(timeoutMs: number): Promise<boolean> {
    if (waiting() === 0 && inFlight.size === 0) return Promise.resolve(true)
    flush()
    return new Promise((resolve) => {
      const done = (): void => {
        clearTimeout(limit)
        waiters.delete(done)
        resolve(true)
      }
      const limit = setTimeout(() => {
        waiters.delete(done)
        resolve(false)
      }, timeoutMs)
      waiters.add(done)
    })
  }

  flush()
  return {
    change,
    flush,
    drain,
    waiting,
    offline: () => failures > 0,
    lastSeq: () => state.seq,
    stop,
  }
}
