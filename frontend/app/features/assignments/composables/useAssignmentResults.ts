// T-11's data: the gradebook, the question stats and the answer key, refreshed together after
// any change (publish, correction, override), and the header's stats line.
import { computed } from 'vue'
import {
  getAnswerKey,
  getGradebook,
  getQuestionStats,
  gradebookCsvUrl,
  unpublishResults,
} from '~/features/assignments/composables/resultsApi'
import { useApiData } from '~/shared/composables/useApiData'
import { formatDecimal } from '~/shared/utils/decimals'

export function useAssignmentResults(assignmentId: string) {
  const book = useApiData(() => getGradebook(assignmentId))
  const stats = useApiData(() => getQuestionStats(assignmentId))
  const keyed = useApiData(() => getAnswerKey(assignmentId))

  async function refresh(): Promise<void> {
    await Promise.all([book.refresh(), stats.refresh(), keyed.refresh()])
  }

  /** "Avg 7 · High 12 · Low 2 · 2 attempted · 1 absent · 0 disq." */
  const statsLine = computed(() => {
    const s = book.data.value?.stats
    if (!s) return ''
    const scores = s.count ? [`Avg ${formatDecimal(s.mean ?? '0')}`, `High ${formatDecimal(s.highest ?? '0')}`, `Low ${formatDecimal(s.lowest ?? '0')}`] : []
    return [...scores, `${s.attempted} attempted`, `${s.absent} absent`, `${s.disqualified} disq.`].join(' · ')
  })

  // What a key correction regrades: every attempt that has ended
  const endedCount = computed(() => (book.data.value?.rows ?? []).filter(r => r.attempt_id && r.status !== 'IN_PROGRESS').length)

  return {
    book,
    stats,
    keyed,
    refresh,
    statsLine,
    endedCount,
    csvUrl: gradebookCsvUrl(assignmentId),
    async unpublish(): Promise<void> {
      await unpublishResults(assignmentId)
      await refresh()
    },
  }
}
