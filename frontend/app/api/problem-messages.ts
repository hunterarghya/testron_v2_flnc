// What the user reads for each problem code (api_contract.md §1). A test fails when a
// code from the catalog has no message here.
import type { ApiProblem } from '~/api/problems'

export const PROBLEM_MESSAGES: Record<string, string> = {
  validation_error: 'Some fields need fixing.',
  not_authenticated: 'Please log in again.',
  forbidden: 'You don\'t have access to this.',
  not_found: 'We couldn\'t find this. It may have been removed.',
  csrf_failed: 'Your session needs refreshing. Reload the page and try again.',
  rate_limited: 'Too many tries. Please wait a moment and try again.',
  invalid_credentials: 'The email or password is not correct.',
  email_not_verified: 'Please verify your email first.',
  otp_invalid: 'That code is not valid. Check it or ask for a new one.',
  password_too_weak: 'Choose a longer, less common password.',
  password_mismatch: 'The two passwords don\'t match.',
  current_password_incorrect: 'Your current password is not correct.',
  account_not_active: 'Your account isn\'t active yet.',
  test_changed_elsewhere: 'This test was changed in another tab. Reload to see the latest version.',
  test_has_problems: 'Fix the problems in this test before assigning it.',
  section_not_empty: 'This section still has questions.',
  tag_exists: 'A tag with this name already exists.',
  group_archived: 'This group is archived. Restore it first.',
  upload_rejected: 'The image was refused. Try again.',
  upload_failed: 'The image couldn\'t be uploaded. Try again.',
  image_type: 'Use a PNG, JPEG, WebP or GIF image.',
  image_too_large: 'Use an image of 5 MB or less.',
  image_not_copied: 'Some pasted images couldn\'t be copied. Upload them instead.',
  image_limit: 'An option holds one image. Remove it first to add another.',
  confirmation_mismatch: 'The confirmation text doesn\'t match.',
  assignment_started: 'This can\'t be changed after the test has started.',
  assignment_cancelled: 'This test was cancelled.',
  assignment_has_attempts: 'Students have already started this test.',
  activation_not_required: 'This test doesn\'t wait for Start.',
  audience_member_has_attempt: 'Some students have already started this test.',
  not_open_yet: 'This test hasn\'t opened yet.',
  waiting_for_teacher: 'Waiting for your teacher to start the test.',
  entry_closed: 'Entry to this test has closed.',
  no_attempts_left: 'You have no attempts left for this test.',
  password_required: 'Enter the test password.',
  password_incorrect: 'That test password is not correct.',
  attempt_ended: 'This test has ended.',
  attempt_taken_over: 'This test was opened on another device.',
  stage_closed: 'This section has closed.',
  question_not_in_stage: 'This question is not open right now.',
  answer_invalid: 'That answer is not in a valid format.',
  stage_navigation_invalid: 'You can\'t move to that section now.',
  results_not_published: 'We couldn\'t find this. It may have been removed.',
  performance_not_shared: 'We couldn\'t find this. It may have been removed.',
  database_unavailable: 'The server is having trouble. Please try again shortly.',
  internal_error: 'Something went wrong on our side.',
  network_error: 'No connection. Check your internet and try again.',
}

const FALLBACK = PROBLEM_MESSAGES.internal_error ?? 'Something went wrong.'

export function problemMessage(problem: ApiProblem): string {
  return PROBLEM_MESSAGES[problem.code] ?? FALLBACK
}
