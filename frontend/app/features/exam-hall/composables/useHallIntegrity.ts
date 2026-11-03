// Leaving the test while in the hall (frontend_spec.md §5.4, P-06). The student is "present"
// when the tab is visible, the window focused and, where it exists, fullscreen is on; any
// signal that changes that opens or closes a departure (engine/integrity.ts). Reports wait
// on this device like answers until acknowledged (the same queue, keyed by event id); the
// server's answer decides: a warning overlay, or the end.
import { onScopeDispose, ref, watch } from 'vue'
import { toProblem } from '~/api/problems'
import type { IntegrityAck } from '~/api/types'
import { createIntegrityWatch, type Departure, type IntegrityKind, type IntegrityWatch } from '~/engine/integrity'
import { createSaveQueue, type SaveQueue, type SendOutcome } from '~/engine/save-queue'
import { reportIntegrity } from '~/features/exam-hall/composables/hallApi'
import { outcomeOf, storageAt } from '~/features/exam-hall/composables/hallQueue'
import type { ExamSession } from '~/features/exam-hall/composables/useExamSession'
import { useServerClock } from '~/shared/composables/useServerClock'
import { integrityKey } from '~/shared/utils/exam-device'
import { canFullscreen, enterFullscreen } from '~/shared/utils/fullscreen'

function present(): boolean {
  return !document.hidden && document.hasFocus() && (!canFullscreen() || Boolean(document.fullscreenElement))
}

function kindNow(): IntegrityKind {
  if (document.hidden) return 'TAB_HIDDEN'
  return canFullscreen() && !document.fullscreenElement ? 'FULLSCREEN_EXIT' : 'WINDOW_BLUR'
}

export function useHallIntegrity(session: ExamSession) {
  const warning = ref(false)
  const serverClock = useServerClock()
  let watcher: IntegrityWatch | null = null
  let queue: SaveQueue<Departure> | null = null
  let listening: [EventTarget, string][] = []

  function acknowledged(ack: IntegrityAck): void {
    session.applyClock(ack)
    if (ack.action === 'ENDED') void session.load()
  }

  async function send(eventId: string, save: { answer: Departure | null }): Promise<SendOutcome> {
    const { kind, left_at, beyond_grace, returned_at } = save.answer!
    try {
      acknowledged(await reportIntegrity(session.attemptId, eventId, { kind, left_at, beyond_grace, returned_at }))
      return 'saved'
    }
    catch (error) {
      return outcomeOf(toProblem(error))
    }
  }

  function onSignal(): void {
    if (present()) watcher?.returned()
    else watcher?.left(kindNow())
  }

  function start(graceS: number): void {
    queue = createSaveQueue<Departure>({
      send,
      storage: storageAt<Departure>(integrityKey(session.attemptId)),
      onStop: () => void session.load(),
      onChange: () => {},
      onDropped: () => {},
    }, 0)
    watcher = createIntegrityWatch({
      graceMs: graceS * 1000,
      now: serverClock.now,
      newId: () => crypto.randomUUID(),
      report: departure => queue?.change(departure.id, departure, false),
      onBeyondGrace: () => {
        warning.value = true
      },
    })
    listening = [[document, 'visibilitychange'], [document, 'fullscreenchange'], [window, 'blur'], [window, 'focus']]
    for (const [target, name] of listening) target.addEventListener(name, onSignal)
    // Back after a refresh, fullscreen is gone: a departure until they return, and the
    // overlay's button at once, so they can be back within the grace period
    if (canFullscreen() && !document.fullscreenElement) {
      onSignal()
      warning.value = true
    }
  }

  function stop(): void {
    watcher?.stop()
    queue?.stop()
    for (const [target, name] of listening) target.removeEventListener(name, onSignal)
    listening = []
  }

  watch(session.phase, (phase) => {
    const live = phase === 'active' || phase === 'review'
    if (live && !watcher && session.state.value) start(session.state.value.integrity.grace_s)
    if (phase === 'ended' || phase === 'taken_over') stop()
  })
  onScopeDispose(stop)

  return {
    warning,
    async returnToTest(): Promise<void> {
      await enterFullscreen()
      warning.value = false
      onSignal()
    },
  }
}
