<!-- A question's header row (T-03): number, type switch, marks (and, per-question tests, time)
     overrides, and ⋯ Duplicate · Move up/down · Delete. Switching to numerical asks first,
     because the options are dropped. -->
<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import { computed, ref } from 'vue'
import type { EditorQuestion, QuestionType, TestSettings } from '~/api/types'
import OverridePopover from '~/features/editor/components/OverridePopover.vue'
import { useEditorContext } from '~/features/editor/composables/editorContext'
import { retyped } from '~/features/editor/utils/question-body'
import ConfirmDialog from '~/shared/components/ConfirmDialog.vue'

const TYPES: { label: string, value: QuestionType }[] = [
  { label: 'MCQ', value: 'MCQ' },
  { label: 'MSQ', value: 'MSQ' },
  { label: 'Numerical', value: 'NUMERICAL' },
]

const props = defineProps<{ number: number, settings: TestSettings, disabled?: boolean }>()
const question = defineModel<EditorQuestion>('question', { required: true })
const emit = defineEmits<{ changed: [] }>()

const { actions } = useEditorContext()
const confirming = ref<'numerical' | 'delete' | null>(null)
const dialogOpen = computed({ get: () => confirming.value !== null, set: (open) => { if (!open) confirming.value = null } })
const perQuestion = computed(() => props.settings.timing.kind === 'PER_QUESTION')
const menu = computed<DropdownMenuItem[]>(() => [
  { label: 'Duplicate', icon: 'i-lucide-copy', onSelect: () => actions.duplicateQuestion(question.value.id) },
  { label: 'Move up', icon: 'i-lucide-arrow-up', onSelect: () => actions.moveQuestion(question.value.id, -1) },
  { label: 'Move down', icon: 'i-lucide-arrow-down', onSelect: () => actions.moveQuestion(question.value.id, 1) },
  { label: 'Delete', icon: 'i-lucide-trash-2', color: 'error', onSelect: () => (confirming.value = 'delete') },
])

function onType(type: QuestionType): void {
  if (type === question.value.type) return
  if (type === 'NUMERICAL' && question.value.options.length) {
    confirming.value = 'numerical'
    return
  }
  retyped(question.value, type)
  emit('changed')
}

function onConfirm(): void {
  if (confirming.value === 'numerical') {
    retyped(question.value, 'NUMERICAL')
    emit('changed')
  }
  else {
    void actions.deleteQuestion(question.value.id)
  }
  confirming.value = null
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <span class="font-semibold">Q{{ number }}</span>
    <USelect
      :model-value="question.type"
      :items="TYPES"
      size="xs"
      class="w-28"
      :disabled="disabled"
      aria-label="Question type"
      @update:model-value="onType"
    />
    <OverridePopover v-model:question="question" :settings="settings" kind="marks" :disabled="disabled" @changed="emit('changed')" />
    <OverridePopover v-if="perQuestion" v-model:question="question" :settings="settings" kind="time" :disabled="disabled" @changed="emit('changed')" />
    <UDropdownMenu :items="menu" :disabled="disabled">
      <UButton icon="i-lucide-ellipsis" color="neutral" variant="ghost" size="xs" class="ms-auto" :aria-label="`More for question ${number}`" />
    </UDropdownMenu>
    <ConfirmDialog
      v-model:open="dialogOpen"
      :title="confirming === 'delete' ? `Delete question ${number}?` : 'Switch to numerical?'"
      :description="confirming === 'delete' ? 'Assigned papers keep their copy; this test loses the question.' : 'Its options are removed. A numerical question has an answer value instead.'"
      :confirm-label="confirming === 'delete' ? 'Delete' : 'Switch'"
      danger
      @confirm="onConfirm"
    />
  </div>
</template>
