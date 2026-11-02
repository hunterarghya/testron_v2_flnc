// "The session expired" as an event: the API client raises it on any 401 not_authenticated,
// and the app shows one "Please log in again" dialog (screens.md §6).

type Listener = () => void

const listeners = new Set<Listener>()

/** Subscribe; returns the function that unsubscribes. */
export function onSessionExpired(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function notifySessionExpired(): void {
  for (const listener of listeners) {
    listener()
  }
}
