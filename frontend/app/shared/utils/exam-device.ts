// What this browser keeps per attempt (frontend_spec.md §5.2, §5.4, §5.7): the exam client
// id the server gave it (so a refresh isn't a takeover), the save queue and the departures
// not yet reported. The gate and the hall both use it. Storage can be unavailable (private
// windows, full disks): then nothing is kept and the hall still works, it just can't
// survive a reload offline.

export const EXAM_CLIENT_HEADER = 'X-Exam-Client'

export function clientKey(attemptId: string): string {
  return `exam:${attemptId}:client`
}

export function queueKey(attemptId: string): string {
  return `exam:${attemptId}:queue`
}

/** Departures not yet acknowledged (P-06), kept like answers */
export function integrityKey(attemptId: string): string {
  return `exam:${attemptId}:integrity`
}

export function readItem(key: string): string | null {
  try {
    return localStorage.getItem(key)
  }
  catch {
    return null
  }
}

export function writeItem(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  }
  catch {
    // Nothing to do: the hall works on without the device copy
  }
}

export function removeItem(key: string): void {
  try {
    localStorage.removeItem(key)
  }
  catch {
    // Already unavailable, so already gone
  }
}

/** The header every attempt request carries, once this device has an id. */
export function examClientHeaders(attemptId: string): Record<string, string> {
  const id = readItem(clientKey(attemptId))
  return id ? { [EXAM_CLIENT_HEADER]: id } : {}
}

/** Keep the id from an attempt state; it changes only when this device takes over. */
export function rememberExamClient(attemptId: string, clientId: string | null | undefined): void {
  if (clientId) writeItem(clientKey(attemptId), clientId)
}

/** The attempt is over or belongs to another device: nothing of it stays here. */
export function forgetAttempt(attemptId: string): void {
  removeItem(clientKey(attemptId))
  removeItem(queueKey(attemptId))
  removeItem(integrityKey(attemptId))
}
