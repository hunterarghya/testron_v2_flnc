<!-- T-03 Import questions ([C-12]): search other tests' questions by text or tag, tick them, and
     copy them in after the question last worked on. Copies are independent of the originals. -->
<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { computed, onScopeDispose, ref, watch } from 'vue'
import { useToast } from '#imports'
import { useEditorContext } from '~/features/editor/composables/editorContext'
import { searchQuestions } from '~/features/editor/composables/editorApi'
import DataTable from '~/shared/components/DataTable.vue'
import { useApiData } from '~/shared/composables/useApiData'
import { plainText } from '~/shared/components/rich-content/plain-text'

type Row = Awaited<ReturnType<typeof searchQuestions>>['items'][number]

const SEARCH_DELAY_MS = 300
const open = defineModel<boolean>('open', { required: true })

const toast = useToast()
const { testId, editor, actions } = useEditorContext()
const search = ref('')
const selected = ref<string[]>([])
const pending = ref(false)
const found = useApiData(() => searchQuestions(testId, search.value))
const columns: TableColumn<Row>[] = [
  { id: 'stem', header: 'Question', cell: ({ row }) => plainText(row.original.stem).slice(0, 140) || '(empty)' },
  { accessorKey: 'type', header: 'Type' },
  { accessorKey: 'test_title', header: 'From test' },
  { id: 'tags', header: 'Tags', cell: ({ row }) => [...row.original.chapter_tags, ...row.original.topic_tags].map(t => t.name).join(', ') },
]

/** After the question last worked on; else at the end of the last section. */
const target = computed(() => {
  const sections = editor.doc.value!.sections
  const current = sections.find(s => s.questions.some(q => q.id === editor.current.value))
  const section = current ?? sections.at(-1)!
  return { sectionId: section.id, afterId: current ? editor.current.value : section.questions.at(-1)?.id ?? null }
})

async function onImport(): Promise<void> {
  pending.value = true
  const count = await actions.importQuestions(selected.value, target.value.sectionId, target.value.afterId)
  pending.value = false
  if (count) {
    toast.add({ title: `${count} question${count === 1 ? '' : 's'} imported`, color: 'success' })
    open.value = false
  }
}

watch(open, (isOpen) => {
  if (!isOpen) return
  search.value = ''
  selected.value = []
  void found.refresh()
}, { immediate: true })
let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => void found.refresh(), SEARCH_DELAY_MS)
})
onScopeDispose(() => clearTimeout(searchTimer))
</script>

<template>
  <UModal v-model:open="open" title="Import questions" description="Copies go in after the question you were last in. Editing a copy never changes the original." :ui="{ content: 'max-w-4xl' }">
    <template #body>
      <div class="space-y-3">
        <UInput v-model="search" icon="i-lucide-search" placeholder="Search question text or tag" class="w-full" aria-label="Search questions" />
        <DataTable
          v-model:selected="selected"
          :rows="found.data.value?.items ?? []"
          :columns="columns"
          :loading="found.pending.value"
          :error="found.error.value"
          empty-title="No questions found in other tests."
          selectable
          @retry="found.refresh"
        />
      </div>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="ghost" @click="open = false" />
        <UButton :label="selected.length ? `Import ${selected.length}` : 'Import'" :disabled="!selected.length" :loading="pending" @click="onImport" />
      </div>
    </template>
  </UModal>
</template>
