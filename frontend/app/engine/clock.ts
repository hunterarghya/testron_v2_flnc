// Server time on the device (frontend_spec.md §5.1). Every response carrying `server_now`
// gives a sample; the offset is the sample whose round trip was shortest, because it is the
// least disturbed by network delay. Countdowns read `remainingMs`, never a counter that
// ticks down, so a sleeping laptop or a throttled tab can't make them drift.

export const MAX_SAMPLES = 5

export interface ClockSample {
  // Server time minus device time, in ms
  offsetMs: number
  rttMs: number
}

/**
 * One sample from a response. `sentAt` and `receivedAt` come from `performance.now()`;
 * `deviceNowMs` is `Date.now()` when the response arrived.
 */
export function sampleFrom(serverNowIso: string, sentAt: number, receivedAt: number, deviceNowMs: number): ClockSample {
  const rttMs = Math.max(0, receivedAt - sentAt)
  // The server read its clock about halfway through the round trip
  const deviceAtServerRead = deviceNowMs - rttMs / 2
  return { offsetMs: Date.parse(serverNowIso) - deviceAtServerRead, rttMs }
}

export function withSample(samples: readonly ClockSample[], sample: ClockSample): ClockSample[] {
  return [...samples, sample].slice(-MAX_SAMPLES)
}

export function offsetOf(samples: readonly ClockSample[]): number {
  let best: ClockSample | undefined
  for (const sample of samples) {
    if (!best || sample.rttMs < best.rttMs) best = sample
  }
  return best?.offsetMs ?? 0
}

export function serverNowMs(samples: readonly ClockSample[], deviceNowMs: number): number {
  return deviceNowMs + offsetOf(samples)
}

export function remainingMs(deadlineIso: string, samples: readonly ClockSample[], deviceNowMs: number): number {
  return Math.max(0, Date.parse(deadlineIso) - serverNowMs(samples, deviceNowMs))
}

/** "00:02:41" for a countdown. */
export function formatCountdown(ms: number): string {
  const total = Math.ceil(ms / 1000)
  const parts = [Math.floor(total / 3600), Math.floor(total / 60) % 60, total % 60]
  return parts.map(part => String(part).padStart(2, '0')).join(':')
}
