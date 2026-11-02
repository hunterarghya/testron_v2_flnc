// T-18's data: every tag with its usage, loaded once (a few hundred at most) and filtered
// here by tab and text. Rename may come back as "merge?" (409 tag_exists).
import { computed, ref } from 'vue'
import { api, unwrap } from '~/api/client'
import { ApiProblem } from '~/api/problems'
import type { TagKind, TagUsage } from '~/api/types'
import { useApiData } from '~/shared/composables/useApiData'

export interface MergeTarget {
  id: string
  name: string
  question_count: number
}

export function mergeTarget(problem: unknown): MergeTarget | null {
  if (!(problem instanceof ApiProblem) || problem.code !== 'tag_exists') {
    return null
  }
  const target = problem.context.target as MergeTarget | undefined
  return target ?? null
}

export function useTags() {
  const kind = ref<TagKind>('CHAPTER')
  const filter = ref('')
  const all = useApiData(() => unwrap(api.GET('/api/v1/admin/tags')))

  const counts = computed(() => {
    const tags = all.data.value ?? []
    return { CHAPTER: tags.filter(tag => tag.kind === 'CHAPTER').length, TOPIC: tags.filter(tag => tag.kind === 'TOPIC').length }
  })
  const shown = computed<TagUsage[]>(() => {
    const typed = filter.value.trim().toLocaleLowerCase()
    return (all.data.value ?? []).filter(tag => tag.kind === kind.value && tag.name.toLocaleLowerCase().includes(typed))
  })

  async function rename(tagId: string, name: string, merge: boolean): Promise<void> {
    await unwrap(api.PATCH('/api/v1/admin/tags/{tag_id}', { params: { path: { tag_id: tagId } }, body: { name, merge } }))
    await all.refresh()
  }

  async function remove(tagId: string): Promise<number> {
    const result = await unwrap(api.DELETE('/api/v1/admin/tags/{tag_id}', { params: { path: { tag_id: tagId } } }))
    await all.refresh()
    return result.removed_from_questions
  }

  return { kind, filter, all, counts, shown, rename, remove }
}
