// The student's own performance report (api_contract.md §2.9; P-10).
import { api, unwrap } from '~/api/client'
import type { Performance } from '~/api/types'

export function getMyPerformance(): Promise<Performance> {
  return unwrap(api.GET('/api/v1/my/performance'))
}
