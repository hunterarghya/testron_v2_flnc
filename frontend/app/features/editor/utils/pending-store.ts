// Saves not yet on the server, kept in this browser per test (editor_content_spec.md §4.4), and
// what is set aside for recovery when another tab changed the test.
import type { PendingStore } from '~/features/editor/utils/save-queue'

const PENDING = 'editor:pending:'
const RECOVERY = 'editor:recovery:'

function read<P>(key: string): Record<string, P> {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as Record<string, P>) : {}
  }
  catch {
    // Storage off (private mode) or a damaged entry: nothing to restore
    return {}
  }
}

function write(key: string, value: Record<string, unknown>): void {
  try {
    if (Object.keys(value).length) localStorage.setItem(key, JSON.stringify(value))
    else localStorage.removeItem(key)
  }
  catch {
    // Storage full or off: saving still works, only the refresh safety net is lost
  }
}

export function pendingStore<P>(testId: string): PendingStore<P> {
  return {
    load: () => read<P>(PENDING + testId),
    save: pending => write(PENDING + testId, pending),
  }
}

/** On "changed elsewhere": the unsaved changes move aside, so a reload starts clean and
 * doesn't overwrite the other tab's work. */
export function setAsideForRecovery(testId: string): void {
  const pending = read<unknown>(PENDING + testId)
  if (Object.keys(pending).length) write(RECOVERY + testId, pending)
  write(PENDING + testId, {})
}

export function recoveryOf(testId: string): Record<string, unknown> {
  return read<unknown>(RECOVERY + testId)
}

export function clearRecovery(testId: string): void {
  write(RECOVERY + testId, {})
}
