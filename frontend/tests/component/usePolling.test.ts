import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope } from 'vue'
import { usePolling } from '~/shared/composables/usePolling'

function setHidden(hidden: boolean): void {
  Object.defineProperty(document, 'hidden', { configurable: true, get: () => hidden })
  document.dispatchEvent(new Event('visibilitychange'))
}

function startPolling(task: () => Promise<unknown>, pauseWhenHidden?: boolean) {
  const scope = effectScope()
  const polling = scope.run(() => usePolling(task, 1000, { pauseWhenHidden }))
  return { scope, polling }
}

describe('usePolling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    setHidden(false)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('runs at once, then every interval', async () => {
    const task = vi.fn(async () => {})
    const { scope } = startPolling(task)

    await vi.advanceTimersByTimeAsync(0)
    expect(task).toHaveBeenCalledTimes(1)
    await vi.advanceTimersByTimeAsync(3000)
    expect(task).toHaveBeenCalledTimes(4)
    scope.stop()
  })

  it('waits for a slow run before scheduling the next', async () => {
    const task = vi.fn(() => new Promise(resolve => setTimeout(resolve, 2500)))
    const { scope } = startPolling(task)

    await vi.advanceTimersByTimeAsync(3000)

    expect(task).toHaveBeenCalledTimes(1)
    scope.stop()
  })

  it('stops when the component goes away', async () => {
    const task = vi.fn(async () => {})
    const { scope } = startPolling(task)
    await vi.advanceTimersByTimeAsync(0)

    scope.stop()
    await vi.advanceTimersByTimeAsync(5000)

    expect(task).toHaveBeenCalledTimes(1)
  })

  it('pauses while the tab is hidden and refreshes on return', async () => {
    const task = vi.fn(async () => {})
    const { scope } = startPolling(task)
    await vi.advanceTimersByTimeAsync(0)

    setHidden(true)
    await vi.advanceTimersByTimeAsync(5000)
    expect(task).toHaveBeenCalledTimes(1)

    setHidden(false)
    await vi.advanceTimersByTimeAsync(0)
    expect(task).toHaveBeenCalledTimes(2)
    scope.stop()
  })

  it('keeps going while hidden when told to (exam hall)', async () => {
    const task = vi.fn(async () => {})
    setHidden(true)
    const { scope } = startPolling(task, false)

    await vi.advanceTimersByTimeAsync(2000)

    expect(task).toHaveBeenCalledTimes(3)
    scope.stop()
  })

  it('refresh runs now without doubling up', async () => {
    const task = vi.fn(async () => {})
    const { scope, polling } = startPolling(task)
    await vi.advanceTimersByTimeAsync(0)

    await polling?.refresh()
    await vi.advanceTimersByTimeAsync(999)

    expect(task).toHaveBeenCalledTimes(2)
    scope.stop()
  })
})
