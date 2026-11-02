<!-- A numerical question's answer and tolerance (T-03): decimal strings, never floats. -->
<script setup lang="ts">
import type { EditorQuestion } from '~/api/types'

defineProps<{ disabled?: boolean }>()
const question = defineModel<EditorQuestion>('question', { required: true })
const emit = defineEmits<{ changed: [], blur: [] }>()

function setAnswer(value: string | number): void {
  question.value.numeric_answer = String(value).trim() || null
  emit('changed')
}

function setTolerance(value: string | number): void {
  question.value.numeric_tolerance = String(value).trim() || '0'
  emit('changed')
}
</script>

<template>
  <div class="flex flex-wrap gap-4">
    <UFormField label="Answer">
      <UInput
        :model-value="question.numeric_answer ?? ''"
        inputmode="decimal"
        placeholder="e.g. 6.02"
        :disabled="disabled"
        @update:model-value="setAnswer"
        @blur="emit('blur')"
      />
    </UFormField>
    <UFormField label="Tolerance (±)">
      <UInput
        :model-value="question.numeric_tolerance"
        inputmode="decimal"
        :disabled="disabled"
        @update:model-value="setTolerance"
        @blur="emit('blur')"
      />
    </UFormField>
  </div>
</template>
