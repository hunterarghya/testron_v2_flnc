// Field-level messages from a problem: `validation_error` lists them per field (api_contract.md §1).
import type { ApiProblem } from '~/api/problems'

export function fieldErrors(problem: ApiProblem | null): Record<string, string> {
  if (!problem || problem.code !== 'validation_error') {
    return {}
  }
  const errors: Record<string, string> = {}
  for (const error of problem.errors) {
    errors[error.field] ??= error.message
  }
  return errors
}
