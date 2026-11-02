<!-- MCQ/MSQ options (T-03): click the radio (MCQ) or checkbox (MSQ) to mark the correct answer;
     letters renumber as options come and go; at least 2 and at most 10 options. -->
<script setup lang="ts">
import type { EditorQuestion } from '~/api/types'
import { newOption, optionLabel } from '~/features/editor/utils/question-body'
import RichField from '~/shared/components/RichField.vue'

const MIN_OPTIONS = 2
const MAX_OPTIONS = 10

defineProps<{ disabled?: boolean }>()
const question = defineModel<EditorQuestion>('question', { required: true })
const emit = defineEmits<{ changed: [], blur: [] }>()

function markCorrect(index: number): void {
  question.value.options.forEach((option, i) => {
    if (question.value.type === 'MCQ') option.is_correct = i === index
    else if (i === index) option.is_correct = !option.is_correct
  })
  emit('changed')
}

function add(): void {
  question.value.options.push(newOption())
  emit('changed')
}

function remove(index: number): void {
  question.value.options.splice(index, 1)
  emit('changed')
}
</script>

<template>
  <div class="space-y-1">
    <div v-for="(option, index) in question.options" :key="option.id" class="flex items-start gap-2">
      <UButton
        :icon="option.is_correct ? (question.type === 'MCQ' ? 'i-lucide-circle-dot' : 'i-lucide-square-check') : (question.type === 'MCQ' ? 'i-lucide-circle' : 'i-lucide-square')"
        :color="option.is_correct ? 'success' : 'neutral'"
        variant="ghost"
        size="sm"
        :aria-label="`Mark option ${optionLabel(index)} correct`"
        :aria-pressed="option.is_correct"
        :disabled="disabled"
        @click="markCorrect(index)"
      />
      <span class="pt-1.5 text-sm font-medium">{{ optionLabel(index) }}</span>
      <div class="min-w-0 flex-1">
        <RichField
          v-model="option.content"
          profile="compact"
          :placeholder="`Option ${optionLabel(index)}`"
          :disabled="disabled"
          @update:model-value="emit('changed')"
          @blur="emit('blur')"
        />
      </div>
      <UButton
        v-if="question.options.length > MIN_OPTIONS"
        icon="i-lucide-x"
        color="neutral"
        variant="ghost"
        size="sm"
        :aria-label="`Remove option ${optionLabel(index)}`"
        :disabled="disabled"
        @click="remove(index)"
      />
    </div>
    <UButton
      v-if="question.options.length < MAX_OPTIONS"
      label="Add option"
      icon="i-lucide-plus"
      color="neutral"
      variant="ghost"
      size="xs"
      :disabled="disabled"
      @click="add"
    />
  </div>
</template>
