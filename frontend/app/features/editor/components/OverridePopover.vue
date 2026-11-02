<!-- A question's own marks or time (T-03 header row): "default" until edited, then "custom";
     "Reset to default" follows Settings again. Marks are decimal strings, never numbers. -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { EditorQuestion, TestSettings } from '~/api/types'
import { formatDecimal } from '~/shared/utils/decimals'

const props = defineProps<{
  settings: TestSettings
  kind: 'marks' | 'time'
  disabled?: boolean
}>()
const question = defineModel<EditorQuestion>('question', { required: true })
const emit = defineEmits<{ changed: [] }>()

const open = ref(false)
const marks = ref('')
const negative = ref('')
const seconds = ref<number | null>(null)
const defaultTime = computed(() => (props.settings.timing.kind === 'PER_QUESTION' ? props.settings.timing.default_question_s : null))
const custom = computed(() => (props.kind === 'marks'
  ? question.value.marks_override !== null || question.value.negative_marks_override !== null
  : question.value.time_override_s !== null))

const label = computed(() => {
  if (props.kind === 'time') {
    return custom.value ? `Time: ${question.value.time_override_s} s (custom)` : `Time: default (${defaultTime.value} s)`
  }
  const right = question.value.marks_override ?? props.settings.marking.marks
  const wrong = question.value.negative_marks_override ?? props.settings.marking.negative_marks
  return `Marks: ${custom.value ? '' : 'default '}(+${formatDecimal(right)}/−${formatDecimal(wrong)})${custom.value ? ' custom' : ''}`
})

watch(open, (isOpen) => {
  if (!isOpen) return
  marks.value = formatDecimal(question.value.marks_override ?? props.settings.marking.marks)
  negative.value = formatDecimal(question.value.negative_marks_override ?? props.settings.marking.negative_marks)
  seconds.value = question.value.time_override_s ?? defaultTime.value
})

function apply(): void {
  if (props.kind === 'marks') {
    question.value.marks_override = marks.value.trim() || null
    question.value.negative_marks_override = negative.value.trim() || null
  }
  else {
    question.value.time_override_s = seconds.value
  }
  open.value = false
  emit('changed')
}

function reset(): void {
  if (props.kind === 'marks') {
    question.value.marks_override = null
    question.value.negative_marks_override = null
  }
  else {
    question.value.time_override_s = null
  }
  open.value = false
  emit('changed')
}
</script>

<template>
  <UPopover v-model:open="open" :disabled="disabled">
    <UButton :label="label" trailing-icon="i-lucide-pencil" size="xs" color="neutral" variant="ghost" />
    <template #content>
      <form class="w-64 space-y-3 p-3" @submit.prevent="apply">
        <template v-if="kind === 'marks'">
          <UFormField label="Right answer (+)">
            <UInput v-model="marks" inputmode="decimal" class="w-full" />
          </UFormField>
          <UFormField label="Wrong answer (−)">
            <UInput v-model="negative" inputmode="decimal" class="w-full" />
          </UFormField>
        </template>
        <UFormField v-else label="Seconds for this question">
          <UInputNumber v-model="seconds" :min="5" :max="3600" class="w-full" />
        </UFormField>
        <div class="flex justify-between gap-2">
          <UButton label="Reset to default" color="neutral" variant="ghost" size="sm" @click="reset" />
          <UButton type="submit" label="Apply" size="sm" />
        </div>
      </form>
    </template>
  </UPopover>
</template>
