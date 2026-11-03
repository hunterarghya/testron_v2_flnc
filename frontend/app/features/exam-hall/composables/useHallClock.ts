// The hall's timer and heartbeat (P-03, api_contract.md §4). The countdown is read from the
// server clock four times a second, never counted down, so a sleeping laptop can't drift.
// At zero the hall sends what it still has and asks the server, which has already ended or
// advanced the attempt at that instant (frontend_spec.md §5.3). Without saves for 15 s, a
// heartbeat brings extensions and "end for everyone".
import { computed, onScopeDispose, ref, watch } from 'vue'
import { toProblem } from '~/api/problems'
import { watchedDeadline } from '~/engine/stage-navigator'
import { heartbeat } from '~/features/exam-hall/composables/hallApi'
import type { ExamSession, HallPhase } from '~/features/exam-hall/composables/useExamSession'
import { usePolling } from '~/shared/composables/usePolling'
import { useServerClock } from '~/shared/composables/useServerClock'

const TICK_MS = 250
export const HEARTBEAT_MS = 15_000
// At zero, unsent answers get this long before the hall asks the server
const FINAL_FLUSH_MS = 3000
// The server may still say "a moment left" if the device's estimate ran ahead: ask again
const RECHECK_MS = 1000
const LIVE: HallPhase[] = ['active', 'review']
// A section that runs out shows "time is over" this long before the next one (P-04, E-2)
export const INTERSTITIAL_MS = 3000

export function useHallClock(session: ExamSession) {
  const serverClock = useServerClock()
  const remainingMs = ref(Number.POSITIVE_INFINITY)
  const nowMs = ref(serverClock.now())
  const interstitial = ref<string | null>(null)
  const deadline = computed(() => (session.clock.value ? watchedDeadline(session.clock.value) : null))
  let handled: string | null = null

  async function reachDeadline(): Promise<void> {
    const before = session.state.value
    await session.drain(FINAL_FLUSH_MS)
    await session.load()
    announceTimeout(before, session.state.value)
    setTimeout(() => {
      handled = null
    }, RECHECK_MS)
  }

  function announceTimeout(before: typeof session.state.value, after: typeof session.state.value): void {
    if (!before || !after || before.timing.kind !== 'SECTIONED' || after.status !== 'IN_PROGRESS') return
    if (before.current_stage_index === after.current_stage_index) return
    const name = (index: number) => after.stage_meta[index]?.title ?? `Section ${index + 1}`
    interstitial.value = `${name(before.current_stage_index)} time is over. Moving to ${name(after.current_stage_index)}…`
    setTimeout(() => {
      interstitial.value = null
    }, INTERSTITIAL_MS)
  }

  function tick(): void {
    nowMs.value = serverClock.now()
    if (!deadline.value || !LIVE.includes(session.phase.value)) return
    remainingMs.value = serverClock.remaining(deadline.value)
    if (remainingMs.value === 0 && handled !== deadline.value) {
      handled = deadline.value
      void reachDeadline()
    }
  }

  async function beat(): Promise<void> {
    const quiet = Date.now() - session.lastContactAt.value >= HEARTBEAT_MS - TICK_MS
    if (!LIVE.includes(session.phase.value) || !quiet) return
    try {
      session.applyClock(await heartbeat(session.attemptId))
    }
    catch (error) {
      session.handleProblem(toProblem(error))
    }
  }

  const ticker = setInterval(tick, TICK_MS)
  // Show the time as soon as a deadline is known, not a tick later
  watch(deadline, tick)
  onScopeDispose(() => clearInterval(ticker))
  // A hidden tab keeps beating: in the hall, leaving is an integrity event anyway
  usePolling(beat, HEARTBEAT_MS, { pauseWhenHidden: false })

  return { remainingMs, deadline, nowMs, interstitial }
}
