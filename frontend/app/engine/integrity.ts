// Leaving the test (frontend_spec.md §5.4). The browser can only notice; the server counts
// and decides. Each departure gets its own id, so a report sent twice is still one event.
// While the student is away, more signals (blur, then the tab hidden) belong to the same
// departure, and leaving again within a second of coming back reopens it too: one alt-tab
// never costs two warnings. A departure reports when it starts, when it outlasts the grace
// period, and when the student comes back.

export type IntegrityKind = 'FULLSCREEN_EXIT' | 'TAB_HIDDEN' | 'WINDOW_BLUR'

export interface Departure {
  id: string
  kind: IntegrityKind
  // ISO times on the server's clock
  left_at: string
  beyond_grace: boolean
  returned_at?: string
}

export interface IntegrityDeps {
  graceMs: number
  // Server time in ms (engine/clock.ts)
  now: () => number
  newId: () => string
  report: (departure: Departure) => void
  // The departure outlasted the grace period: show the warning overlay
  onBeyondGrace: (departure: Departure) => void
}

export interface IntegrityWatch {
  left: (kind: IntegrityKind) => void
  returned: () => void
  away: () => boolean
  stop: () => void
}

// Signals this close together are one departure
export const COALESCE_MS = 1000

export function createIntegrityWatch(deps: IntegrityDeps): IntegrityWatch {
  let open: Departure | null = null
  let closed: { departure: Departure, at: number } | null = null
  let grace: ReturnType<typeof setTimeout> | undefined
  let stopped = false

  function iso(ms: number): string {
    return new Date(ms).toISOString()
  }

  function startGrace(departure: Departure): void {
    clearTimeout(grace)
    // Coming back clears this timer, so when it fires the student is still away
    grace = setTimeout(() => {
      departure.beyond_grace = true
      deps.report({ ...departure })
      deps.onBeyondGrace({ ...departure })
    }, deps.graceMs)
  }

  function left(kind: IntegrityKind): void {
    if (stopped || open) return
    const now = deps.now()
    if (closed && now - closed.at < COALESCE_MS) {
      open = closed.departure
      delete open.returned_at
    }
    else {
      open = { id: deps.newId(), kind, left_at: iso(now), beyond_grace: false }
      deps.report({ ...open })
    }
    closed = null
    if (!open.beyond_grace) startGrace(open)
  }

  function returned(): void {
    if (stopped || !open) return
    const now = deps.now()
    clearTimeout(grace)
    open.returned_at = iso(now)
    deps.report({ ...open })
    closed = { departure: open, at: now }
    open = null
  }

  return {
    left,
    returned,
    away: () => open !== null,
    stop: () => {
      stopped = true
      clearTimeout(grace)
    },
  }
}
