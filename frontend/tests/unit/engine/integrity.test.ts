import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { COALESCE_MS, createIntegrityWatch, type Departure } from '~/engine/integrity'

const T0 = Date.parse('2026-11-12T04:30:00Z')

function harness(graceMs = 5000) {
  let now = T0
  let ids = 0
  const reports: Departure[] = []
  const warnings: Departure[] = []
  const watch = createIntegrityWatch({
    graceMs,
    now: () => now,
    newId: () => `e${++ids}`,
    report: d => reports.push(d),
    onBeyondGrace: d => warnings.push(d),
  })
  const pass = (ms: number) => {
    now += ms
    vi.advanceTimersByTime(ms)
  }
  return { watch, reports, warnings, pass }
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('integrity watch (frontend_spec.md §5.4)', () => {
  it('a short absence is reported, then closed, without a warning', () => {
    const { watch, reports, warnings, pass } = harness()

    watch.left('TAB_HIDDEN')
    expect(watch.away()).toBe(true)
    pass(2000)
    watch.returned()

    expect(reports).toEqual([
      { id: 'e1', kind: 'TAB_HIDDEN', left_at: '2026-11-12T04:30:00.000Z', beyond_grace: false },
      { id: 'e1', kind: 'TAB_HIDDEN', left_at: '2026-11-12T04:30:00.000Z', beyond_grace: false, returned_at: '2026-11-12T04:30:02.000Z' },
    ])
    expect(warnings).toEqual([])
    expect(watch.away()).toBe(false)
  })

  it('staying away past the grace period reports it and warns once', () => {
    const { watch, reports, warnings, pass } = harness()

    watch.left('FULLSCREEN_EXIT')
    pass(5000)
    pass(5000)
    watch.returned()

    expect(reports.map(r => [r.beyond_grace, r.returned_at !== undefined])).toEqual([[false, false], [true, false], [true, true]])
    expect(warnings).toHaveLength(1)
  })

  it('blur then hidden is one departure', () => {
    const { watch, reports } = harness()

    watch.left('WINDOW_BLUR')
    watch.left('TAB_HIDDEN')

    expect(reports.map(r => [r.id, r.kind])).toEqual([['e1', 'WINDOW_BLUR']])
  })

  it('leaving again within a second of coming back is the same departure', () => {
    const { watch, reports, warnings, pass } = harness()

    watch.left('WINDOW_BLUR')
    pass(100)
    watch.returned()
    pass(COALESCE_MS - 1)
    watch.left('TAB_HIDDEN')
    pass(5000)

    expect(new Set(reports.map(r => r.id))).toEqual(new Set(['e1']))
    expect(warnings).toHaveLength(1)
    pass(COALESCE_MS)
    watch.returned()
    pass(COALESCE_MS)
    watch.left('TAB_HIDDEN')
    expect(reports.at(-1)!.id).toBe('e2')
  })

  it('a departure already warned is not warned again when reopened', () => {
    const { watch, warnings, pass } = harness()

    watch.left('TAB_HIDDEN')
    pass(6000)
    watch.returned()
    watch.left('TAB_HIDDEN')
    pass(6000)

    expect(warnings).toHaveLength(1)
  })

  it('coming back without having left does nothing, and a stopped watch ignores everything', () => {
    const { watch, reports, pass } = harness()

    watch.returned()
    watch.left('TAB_HIDDEN')
    watch.stop()
    pass(10_000)
    watch.returned()
    watch.left('WINDOW_BLUR')

    expect(reports).toHaveLength(1)
  })
})
