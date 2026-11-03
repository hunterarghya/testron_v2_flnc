// P-02's state: the gate from the server (polled every 5 s while waiting, which also keeps
// the student "Joined" in the teacher's lobby), whether the rules were read, and the
// countdown to a scheduled start, read from the server clock.
import { computed, onScopeDispose, ref } from 'vue'
import type { GateState } from '~/api/types'
import { getGate } from '~/features/my-tests/composables/myTestsApi'
import { useApiData } from '~/shared/composables/useApiData'
import { usePolling } from '~/shared/composables/usePolling'
import { useServerClock } from '~/shared/composables/useServerClock'

// api_contract.md §4: the gate polls every 5 s while waiting
const GATE_INTERVAL_MS = 5000
// Countdowns redraw 4 times a second (frontend_spec.md §5.1)
const TICK_MS = 250
// At zero, wait up to 1.5 s at random so a whole class doesn't ask at the same instant
const SPREAD_MS = 1500
const WAITING: GateState['state'][] = ['WAITING_FOR_TEACHER', 'NOT_OPEN']

export function useGate(assignmentId: string) {
  const gate = useApiData(() => getGate(assignmentId))
  const clock = useServerClock()
  const rulesRead = ref(false)
  const remainingMs = ref(0)
  const state = computed(() => gate.data.value?.state)
  let atZero: ReturnType<typeof setTimeout> | undefined

  function tick(): void {
    const opensAt = gate.data.value?.opens_at
    if (state.value !== 'NOT_OPEN' || !opensAt) return
    const before = remainingMs.value
    remainingMs.value = clock.remaining(opensAt)
    if (remainingMs.value === 0 && before !== 0) {
      atZero = setTimeout(() => void gate.refresh(), Math.random() * SPREAD_MS)
    }
  }

  const ticker = setInterval(tick, TICK_MS)
  onScopeDispose(() => {
    clearInterval(ticker)
    clearTimeout(atZero)
  })
  usePolling(async () => {
    if (!gate.data.value || WAITING.includes(gate.data.value.state)) await gate.refresh()
  }, GATE_INTERVAL_MS)

  return { gate, state, rulesRead, remainingMs }
}
