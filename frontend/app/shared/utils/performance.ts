// Drawing helpers for performance reports (P-10, T-15, T-17). Percentages arrive as decimal
// strings; they become numbers here only to size bars and plot the trend, never for marks.

export interface TrendItem { label: string, ended_at: string, score_pct: string }

export const CHART = { width: 300, height: 100 } as const

/** A bar's fill: scores below zero show as an empty bar, never a negative one. */
export function barValue(pct: string): number {
  return Math.min(100, Math.max(0, Number(pct)))
}

/** Weak chapters stand out: red under 40 %, amber under 70 %, green from there. */
export function barColor(pct: string): 'error' | 'warning' | 'success' {
  const value = Number(pct)
  if (value < 40) return 'error'
  return value < 70 ? 'warning' : 'success'
}

/** Where each test sits on the chart, oldest on the left. Zero and 100 % always fit, and so
 *  does a negative score. A single test sits in the middle. */
export function trendPoints(items: readonly TrendItem[]): { x: number, y: number }[] {
  const values = items.map(item => Number(item.score_pct))
  const low = Math.min(0, ...values)
  const high = Math.max(100, ...values)
  const step = items.length > 1 ? CHART.width / (items.length - 1) : 0
  return values.map((value, index) => ({
    x: items.length > 1 ? index * step : CHART.width / 2,
    y: CHART.height - ((value - low) / (high - low)) * CHART.height,
  }))
}

const plural = (count: number, word: string): string => `${count} ${word}${count === 1 ? '' : 's'}`

/** "Based on 9 published tests" (P-10), or every graded test for the teacher (T-15). */
export function basisText(attempts: number, published: boolean): string {
  return `Based on ${plural(attempts, published ? 'published test' : 'graded test')}`
}

/** T-17: the group's attempts, and whose they are. */
export function groupBasisText(attempts: number, students: number): string {
  return `Based on ${plural(attempts, 'graded attempt')} by ${plural(students, 'student')}. The trend is each test's class score.`
}
