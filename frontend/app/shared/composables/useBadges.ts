// The counts on the teacher's menu (pending students, results to publish), refreshed every
// 60 s (api_contract.md §4) and after actions that change them.
import { useState } from '#imports'
import { api, unwrap } from '~/api/client'
import type { Badges } from '~/api/types'

export const BADGES_INTERVAL_MS = 60_000

export function useBadges() {
  const badges = useState<Badges | null>('teacher-badges', () => null)

  async function refresh(): Promise<void> {
    badges.value = await unwrap(api.GET('/api/v1/admin/badges'))
  }

  return { badges, refresh }
}
