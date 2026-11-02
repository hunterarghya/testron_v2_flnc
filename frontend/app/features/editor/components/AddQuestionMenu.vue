<!-- "+ Add question" (T-03): MCQ, MSQ or Numerical after the given question, and, in sectioned
     tests, a new section. Inside a question's text, "/" offers the same (T-03). -->
<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import { computed } from 'vue'
import type { QuestionType } from '~/api/types'
import { useEditorContext } from '~/features/editor/composables/editorContext'
import { focusQuestion } from '~/features/editor/utils/focus'

const props = defineProps<{ sectionId: string, afterId: string | null, sectioned: boolean }>()

const { editor, actions } = useEditorContext()

async function add(type: QuestionType): Promise<void> {
  const id = await actions.addQuestion(type, props.sectionId, props.afterId)
  // Straight to typing the question
  if (id) focusQuestion(id)
}

const items = computed<DropdownMenuItem[][]>(() => [
  [
    { label: 'MCQ (single correct)', icon: 'i-lucide-circle-dot', onSelect: () => add('MCQ') },
    { label: 'MSQ (multiple correct)', icon: 'i-lucide-square-check', onSelect: () => add('MSQ') },
    { label: 'Numerical', icon: 'i-lucide-hash', onSelect: () => add('NUMERICAL') },
  ],
  props.sectioned ? [{ label: 'Section', icon: 'i-lucide-separator-horizontal', onSelect: () => actions.addSection(props.sectionId) }] : [],
])
</script>

<template>
  <UDropdownMenu :items="items" :disabled="editor.readOnly.value">
    <UButton label="Add question" icon="i-lucide-plus" color="neutral" variant="ghost" size="sm" />
  </UDropdownMenu>
</template>
