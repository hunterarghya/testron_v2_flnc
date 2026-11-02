// The coaching centre's name and logo, shown in every header (GET /app). Loaded once and
// shared; Settings › Branding puts its saved values here so headers change at once.
import { useState } from '#imports'
import { api, unwrap } from '~/api/client'
import type { AppInfo } from '~/api/types'

export function useAppInfo() {
  const info = useState<AppInfo | null>('app-info', () => null)

  async function load(): Promise<void> {
    info.value = await unwrap(api.GET('/api/v1/app'))
  }

  function set(next: AppInfo): void {
    info.value = { coaching_name: next.coaching_name, logo_url: next.logo_url }
  }

  return { info, load, set }
}
