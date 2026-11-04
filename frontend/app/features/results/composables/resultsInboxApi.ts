// The teacher's results inbox and dashboard (api_contract.md §2.2, §2.7; T-13, T-01).
import { api, unwrap } from '~/api/client'
import type { Dashboard, ResultsInboxPage } from '~/api/types'

export type InboxTab = 'to_publish' | 'published' | 'all'

export function listResultsInbox(tab: InboxTab): Promise<ResultsInboxPage> {
  return unwrap(api.GET('/api/v1/admin/results', { params: { query: { tab, page: 1, page_size: 200 } } }))
}

export function getDashboard(): Promise<Dashboard> {
  return unwrap(api.GET('/api/v1/admin/dashboard'))
}
