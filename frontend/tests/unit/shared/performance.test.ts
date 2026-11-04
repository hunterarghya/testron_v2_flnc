import { describe, expect, it } from 'vitest'
import { barColor, barValue, basisText, CHART, groupBasisText, trendPoints } from '~/shared/utils/performance'

const at = (score_pct: string) => ({ label: 'T', ended_at: '2026-11-12T05:00:00Z', score_pct })

describe('performance drawing (P-10, T-15, T-17)', () => {
  it('fills bars between empty and full, and colours the weak ones', () => {
    expect([barValue('-25.0'), barValue('42.5'), barValue('100.0')]).toEqual([0, 42.5, 100])
    expect([barColor('39.9'), barColor('40.0'), barColor('70.0')]).toEqual(['error', 'warning', 'success'])
  })

  it('plots oldest left, 100 % at the top, and makes room for a negative score', () => {
    expect(trendPoints([at('0.0'), at('100.0')])).toEqual([{ x: 0, y: CHART.height }, { x: CHART.width, y: 0 }])
    const [low] = trendPoints([at('-25.0'), at('100.0')])
    expect(low!.y).toBe(CHART.height)
    expect(trendPoints([at('50.0')])).toEqual([{ x: CHART.width / 2, y: CHART.height / 2 }])
  })

  it('says what the report is based on', () => {
    expect(basisText(1, true)).toBe('Based on 1 published test')
    expect(basisText(3, false)).toBe('Based on 3 graded tests')
    expect(groupBasisText(4, 2)).toBe('Based on 4 graded attempts by 2 students. The trend is each test\'s class score.')
  })
})
