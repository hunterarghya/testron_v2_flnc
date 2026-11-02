// The editor's save queue (editor_content_spec.md §4.4, frontend_spec.md §4): every change to a
// test goes through it, one at a time, each based on the revision the previous one returned.
//
// - Saves have a key (one per question, section or the test itself). A newer save of the same
//   key replaces one still waiting, so typing never piles up requests.
// - Waiting saves are mirrored to storage, so a refresh doesn't lose them.
// - No connection: the save is retried with backoff and the status is "offline".
// - "Changed elsewhere" (another tab): everything stops; the user reloads.
// - Structural changes (add, delete, reorder) are tasks: they wait their turn but aren't
//   merged, stored or retried (repeating them could do the work twice).
import { ApiProblem, NETWORK_ERROR } from '~/api/problems'

export type SaveStatus = 'saved' | 'saving' | 'offline' | 'conflict' | 'failed'

export interface Mutation {
  revision: number
}

export interface PendingStore<P> {
  load: () => Record<string, P>
  save: (pending: Record<string, P>) => void
}

export interface SaveQueueOptions<P> {
  revision: number
  send: (payload: P, revision: number) => Promise<Mutation>
  onSaved?: (key: string, result: Mutation) => void
  onFailed?: (key: string, problem: ApiProblem) => void
  onStatus?: (status: SaveStatus) => void
  store?: PendingStore<P>
  wait?: (ms: number) => Promise<void>
}

export const CONFLICT = 'test_changed_elsewhere'
const RETRY_DELAYS_MS = [1000, 2000, 4000, 8000, 15000, 30000]

type Item
  = | { kind: 'save', key: string }
    | { kind: 'task', task: (revision: number) => Promise<Mutation>, settle: (outcome: Promise<Mutation>) => void }

const defaultWait = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms))

export class SaveQueue<P> {
  revision: number
  private readonly items: Item[] = []
  private readonly pending: Map<string, P>
  private running = false
  private offline = false
  private conflict = false
  private lastFailed = false
  private readonly wait: (ms: number) => Promise<void>

  constructor(private readonly options: SaveQueueOptions<P>) {
    this.revision = options.revision
    this.wait = options.wait ?? defaultWait
    this.pending = new Map(Object.entries(options.store?.load() ?? {}))
    for (const key of this.pending.keys()) {
      this.items.push({ kind: 'save', key })
    }
    void this.drain()
  }

  get status(): SaveStatus {
    if (this.conflict) return 'conflict'
    if (this.offline) return 'offline'
    if (this.items.length > 0 || this.running) return 'saving'
    return this.lastFailed ? 'failed' : 'saved'
  }

  /** Has a save for `key` not reached the server yet? */
  isPending(key: string): boolean {
    return this.pending.has(key)
  }

  save(key: string, payload: P): void {
    const waiting = this.pending.has(key) && this.items.some(item => item.kind === 'save' && item.key === key)
    this.pending.set(key, payload)
    this.persist()
    if (!waiting) {
      this.items.push({ kind: 'save', key })
    }
    void this.drain()
  }

  run<T extends Mutation>(task: (revision: number) => Promise<T>): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      this.items.push({
        kind: 'task',
        task,
        settle: outcome => outcome.then(result => resolve(result as T), reject),
      })
      void this.drain()
    })
  }

  private async drain(): Promise<void> {
    if (this.running || this.conflict) return
    this.running = true
    this.notify()
    while (this.items.length > 0 && !this.conflict) {
      const item = this.items.shift()!
      await (item.kind === 'save' ? this.runSave(item.key) : this.runTask(item))
      this.notify()
    }
    this.running = false
    this.notify()
  }

  private async runSave(key: string): Promise<void> {
    for (let attempt = 0; ; attempt++) {
      const payload = this.pending.get(key)
      if (payload === undefined) return
      try {
        const result = await this.options.send(payload, this.revision)
        this.accept(result)
        // Typed again while this was in flight: that newer payload is queued already
        if (this.pending.get(key) === payload) this.pending.delete(key)
        this.persist()
        this.options.onSaved?.(key, result)
        return
      }
      catch (caught) {
        if (!(await this.recover(problemOf(caught), attempt, key))) return
      }
    }
  }

  /** True to try the same save again. */
  private async recover(problem: ApiProblem, attempt: number, key: string): Promise<boolean> {
    if (problem.code === NETWORK_ERROR) {
      this.offline = true
      this.notify()
      await this.wait(RETRY_DELAYS_MS[Math.min(attempt, RETRY_DELAYS_MS.length - 1)]!)
      return true
    }
    if (problem.code === CONFLICT) {
      this.conflict = true
      // Kept (and stored) for the user to recover after reloading
      this.items.unshift({ kind: 'save', key })
      return false
    }
    this.pending.delete(key)
    this.persist()
    this.lastFailed = true
    this.options.onFailed?.(key, problem)
    return false
  }

  private async runTask(item: Extract<Item, { kind: 'task' }>): Promise<void> {
    const outcome = item.task(this.revision)
    try {
      this.accept(await outcome)
    }
    catch (caught) {
      if (problemOf(caught).code === CONFLICT) this.conflict = true
    }
    item.settle(outcome)
  }

  private accept(result: Mutation): void {
    this.revision = result.revision
    this.offline = false
    this.lastFailed = false
  }

  private persist(): void {
    this.options.store?.save(Object.fromEntries(this.pending))
  }

  private notify(): void {
    this.options.onStatus?.(this.status)
  }
}

function problemOf(caught: unknown): ApiProblem {
  return caught instanceof ApiProblem
    ? caught
    : new ApiProblem({ status: 0, code: 'internal_error', detail: String(caught) })
}
