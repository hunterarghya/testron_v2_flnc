import { describe, expect, it } from 'vitest'
import { PROBLEM_MESSAGES, problemMessage } from '~/api/problem-messages'
import { ApiProblem, networkProblem, toProblem } from '~/api/problems'

// api_contract.md §1 catalog, plus the codes the client and /healthz add
const CATALOG = [
  'validation_error', 'not_authenticated', 'forbidden', 'not_found', 'csrf_failed',
  'rate_limited', 'invalid_credentials', 'email_not_verified', 'otp_invalid',
  'password_too_weak', 'password_mismatch', 'current_password_incorrect',
  'account_not_active', 'test_changed_elsewhere', 'test_has_problems', 'section_not_empty',
  'tag_exists', 'confirmation_mismatch', 'assignment_started', 'assignment_cancelled',
  'assignment_has_attempts', 'audience_member_has_attempt', 'not_open_yet',
  'waiting_for_teacher', 'entry_closed', 'no_attempts_left', 'password_required',
  'password_incorrect', 'attempt_ended', 'attempt_taken_over', 'stage_closed',
  'question_not_in_stage', 'answer_invalid', 'stage_navigation_invalid',
  'results_not_published', 'performance_not_shared', 'database_unavailable',
  'internal_error', 'network_error',
]

const problem = (code: string) => new ApiProblem({ status: 409, code, detail: 'x' })

describe('problem messages', () => {
  it.each(CATALOG)('%s has a message', (code) => {
    expect(PROBLEM_MESSAGES[code]).toBeTruthy()
  })

  it('an unknown code gets the generic message', () => {
    expect(problemMessage(problem('brand_new_code'))).toBe(PROBLEM_MESSAGES.internal_error)
  })

  it('hidden results read exactly like a missing page', () => {
    expect(problemMessage(problem('results_not_published')))
      .toBe(problemMessage(problem('not_found')))
  })
})

describe('toProblem', () => {
  it('passes an ApiProblem through', () => {
    const offline = networkProblem()

    expect(toProblem(offline)).toBe(offline)
  })

  it('re-throws anything else, so bugs are not hidden as API errors', () => {
    const bug = new TypeError('undefined is not a function')

    expect(() => toProblem(bug)).toThrow(bug)
  })
})
