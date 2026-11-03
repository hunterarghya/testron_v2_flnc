import { describe, expect, it } from 'vitest'
import {
  MAX_SAMPLES,
  formatCountdown,
  offsetOf,
  remainingMs,
  sampleFrom,
  serverNowMs,
  withSample,
} from '~/engine/clock'

const SERVER = '2026-11-12T05:00:00.000Z'
const SERVER_MS = Date.parse(SERVER)

describe('sampleFrom', () => {
  it('measures the offset at the middle of the round trip', () => {
    // Sent at 100, received at 300: the server read its clock 100 ms before arrival
    const sample = sampleFrom(SERVER, 100, 300, SERVER_MS - 5000 + 100)
    expect(sample).toEqual({ offsetMs: 5000, rttMs: 200 })
  })

  it('never counts a negative round trip', () => {
    expect(sampleFrom(SERVER, 300, 100, SERVER_MS).rttMs).toBe(0)
  })
})

describe('offset', () => {
  it('is 0 with no samples, and the shortest round trip wins', () => {
    expect(offsetOf([])).toBe(0)
    expect(offsetOf([{ offsetMs: 900, rttMs: 400 }, { offsetMs: 1000, rttMs: 50 }, { offsetMs: 1100, rttMs: 60 }])).toBe(1000)
  })

  it(`keeps the last ${MAX_SAMPLES} samples`, () => {
    let samples = [{ offsetMs: 1, rttMs: 1 }]
    for (let i = 0; i < MAX_SAMPLES; i++) samples = withSample(samples, { offsetMs: 2, rttMs: 10 })
    expect(samples).toHaveLength(MAX_SAMPLES)
    expect(offsetOf(samples)).toBe(2)
  })
})

describe('countdowns', () => {
  const samples = [{ offsetMs: 60_000, rttMs: 10 }]

  it('read server time, not the device clock', () => {
    expect(serverNowMs(samples, SERVER_MS)).toBe(SERVER_MS + 60_000)
    expect(remainingMs('2026-11-12T05:03:00Z', samples, SERVER_MS)).toBe(120_000)
  })

  it('stop at zero', () => {
    expect(remainingMs('2026-11-12T04:00:00Z', samples, SERVER_MS)).toBe(0)
  })

  it('format as hours, minutes, seconds, rounding up', () => {
    expect(formatCountdown(161_000)).toBe('00:02:41')
    expect(formatCountdown(3_600_500)).toBe('01:00:01')
    expect(formatCountdown(0)).toBe('00:00:00')
  })
})
