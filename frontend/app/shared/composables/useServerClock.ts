// The app's one server clock (frontend_spec.md §5.1): `measure` a call whose answer carries
// `server_now`, and read `now()` / `remaining()` anywhere. Samples live for the whole visit.
import { ref } from 'vue'
import { type ClockSample, remainingMs, sampleFrom, serverNowMs, withSample } from '~/engine/clock'

const samples = ref<ClockSample[]>([])

export function useServerClock() {
  async function measure<T extends { server_now: string }>(call: () => Promise<T>): Promise<T> {
    const sentAt = performance.now()
    const answer = await call()
    samples.value = withSample(samples.value, sampleFrom(answer.server_now, sentAt, performance.now(), Date.now()))
    return answer
  }

  return {
    measure,
    now: () => serverNowMs(samples.value, Date.now()),
    remaining: (deadlineIso: string) => remainingMs(deadlineIso, samples.value, Date.now()),
  }
}
