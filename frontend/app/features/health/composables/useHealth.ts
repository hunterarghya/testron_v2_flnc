import { api, unwrap } from '~/api/client'
import type { components } from '~/api/schema'
import { type ApiData, useApiData } from '~/shared/composables/useApiData'

export type Health = components['schemas']['HealthOut']

export function useHealth(): ApiData<Health> {
  return useApiData(() => unwrap(api.GET('/api/v1/healthz')))
}
