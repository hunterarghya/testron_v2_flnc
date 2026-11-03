// What the gate says (P-02): the rules before starting and the late-joiner message.
import { problemMessage } from '~/api/problem-messages'
import type { ApiProblem } from '~/api/problems'
import type { GateState } from '~/api/types'
import { formatDuration, formatTime } from '~/shared/utils/time'

type Rules = GateState['rules']

/** "30 Qs · 120 marks · 50 min" */
export function rulesFacts(rules: Rules): string {
  return `${rules.question_count} Qs · ${Number(rules.total_marks)} marks · ${formatDuration(rules.total_duration_s)}`
}

/** "Sections: Botany 20 min · Zoology 30 min", or null when there's one stage per question. */
export function stagesLine(rules: Rules): string | null {
  if (rules.timing_kind !== 'SECTIONED') return null
  return `Sections: ${rules.stages.map(stage => `${stage.title ?? 'Section'} ${formatDuration(stage.duration_s)}`).join(' · ')}`
}

/** "Marking: +4 / −1", or the per-question note when marks differ. */
export function markingLine(rules: Rules): string {
  if (rules.marking === 'MIXED') return 'Marking: shown with each question'
  return `Marking: +${Number(rules.marking.marks)} / −${Number(rules.marking.negative_marks)}`
}

export function ruleBullets(rules: Rules): string[] {
  const action = rules.action === 'DISQUALIFY' ? 'disqualification' : 'auto-submit'
  const bullets = [
    'The test opens in fullscreen.',
    `Leaving fullscreen or switching apps counts as a warning (${rules.max_warnings} warnings → ${action}).`,
  ]
  if (rules.timing_kind === 'PER_QUESTION') bullets.push('Each question has its own timer. You can\'t go back.')
  else if (rules.timing_kind === 'SECTIONED' && !rules.allow_return) bullets.push('You can\'t go back to a section after leaving it.')
  return bullets
}

/** P-02's late joiner: "You have 44 min. Entry closes at 10:10." Null when it isn't late. */
export function lateJoinMessage(gate: GateState): string | null {
  const left = gate.time_remaining_if_started_now_s
  if (gate.state !== 'READY' || left == null || left >= gate.rules.total_duration_s) return null
  const cutOff = gate.late_entry_until ? ` Entry closes at ${formatTime(gate.late_entry_until)}.` : ''
  return `The test has already started. You have ${formatDuration(left)}.${cutOff}`
}

/** Why Start didn't work, in words: tries left after a wrong password, or how long to wait. */
export function startProblemText(problem: ApiProblem): string {
  if (problem.code === 'password_incorrect' && typeof problem.context.tries_left === 'number') {
    const left = problem.context.tries_left
    return `That password isn't right. ${left} ${left === 1 ? 'try' : 'tries'} left.`
  }
  if (problem.code === 'rate_limited' && typeof problem.context.retry_after_s === 'number') {
    return `Too many tries. Try again in ${problem.context.retry_after_s} s.`
  }
  return problemMessage(problem)
}
