// The active groups, for the group pickers and filters on several screens (T-06, T-07, T-14).
import { api, unwrap } from '~/api/client'
import type { Group } from '~/api/types'
import { type ApiData, useApiData } from '~/shared/composables/useApiData'

export function useActiveGroups(): ApiData<Group[]> {
  return useApiData(() => unwrap(api.GET('/api/v1/admin/groups', { params: { query: { archived: false } } })))
}
