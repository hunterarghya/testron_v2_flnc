// Accessibility checks for component tests (testing_strategy.md "a11y", ADR-085): axe-core
// over a mounted screen, failing on serious or critical problems only. Colour contrast needs
// real layout, which the test DOM doesn't have; it is a manual check in browser_checklist.md.
import axe from 'axe-core'

const OFF = { 'color-contrast': { enabled: false } }

/** "rule-id: selector, selector" for each serious or critical violation in `root`. */
export async function seriousViolations(root: Element): Promise<string[]> {
  const result = await axe.run(root, { rules: OFF, resultTypes: ['violations'] })
  return result.violations
    .filter(v => v.impact === 'serious' || v.impact === 'critical')
    .map(v => `${v.id}: ${v.nodes.map(node => node.target.join(' ')).join(', ')}`)
}
