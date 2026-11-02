// Run a task now and then every `intervalMs` until the component goes away
// (frontend_spec.md §3; the intervals are in api_contract.md §4).
//
// The next run is scheduled only after the previous one finishes, so slow responses never
// pile up. While the tab is hidden nothing runs (unless pauseWhenHidden is false, as in the
// exam hall); when it becomes visible again, it runs at once so the screen is fresh.
import { onScopeDispose } from 'vue'

export interface PollingOptions {
  pauseWhenHidden?: boolean
}

export interface Polling {
  refresh: () => Promise<void>
  stop: () => void
}

export function usePolling(task: () => Promise<unknown>, intervalMs: number, options: PollingOptions = {}): Polling {
  const pauseWhenHidden = options.pauseWhenHidden ?? true
  let timer: ReturnType<typeof setTimeout> | undefined
  let active = true
  let running = false

  async function run(): Promise<void> {
    clearTimeout(timer)
    if (!active || running || (pauseWhenHidden && document.hidden)) {
      return
    }
    running = true
    try {
      await task()
    }
    finally {
      running = false
      if (active) {
        timer = setTimeout(run, intervalMs)
      }
    }
  }

  function onVisibilityChange(): void {
    if (!document.hidden) {
      void run()
    }
  }

  function stop(): void {
    active = false
    clearTimeout(timer)
    document.removeEventListener('visibilitychange', onVisibilityChange)
  }

  if (pauseWhenHidden) {
    document.addEventListener('visibilitychange', onVisibilityChange)
  }
  onScopeDispose(stop)
  void run()
  return { refresh: run, stop }
}
