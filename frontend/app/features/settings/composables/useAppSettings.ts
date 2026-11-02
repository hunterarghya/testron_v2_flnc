// T-19's data: the teacher's defaults and branding. Saving the branding also updates the
// header everyone sees (useAppInfo), without a reload.
import { api, unwrap } from '~/api/client'
import type { AppSettings, AppSettingsChanges } from '~/api/types'
import { useApiData } from '~/shared/composables/useApiData'
import { useAppInfo } from '~/shared/composables/useAppInfo'

export function useAppSettings() {
  const app = useAppInfo()
  const settings = useApiData(() => unwrap(api.GET('/api/v1/admin/settings')))

  async function save(changes: AppSettingsChanges): Promise<AppSettings> {
    const saved = await unwrap(api.PATCH('/api/v1/admin/settings', { body: changes }))
    settings.data.value = saved
    app.set(saved)
    return saved
  }

  return { settings, save }
}
