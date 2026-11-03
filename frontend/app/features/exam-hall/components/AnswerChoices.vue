<!-- A choice question's options (P-03), in the student's shuffled order with labels A, B, …
     One answer for MCQ, any number for MSQ. Every pick is saved at once [F-2]. -->
<script setup lang="ts">
import { computed } from 'vue'
import type { HallAnswer, HallQuestion } from '~/api/types'
import RichContentView from '~/shared/components/rich-content/RichContentView.vue'

const props = defineProps<{ question: HallQuestion, answer: HallAnswer | null }>()
const emit = defineEmits<{ change: [answer: HallAnswer | null] }>()

const items = computed(() => props.question.options.map(option => ({ value: option.id, label: option.label })))
const contents = computed(() => new Map(props.question.options.map(option => [option.id, option.content])))
const picked = computed(() => (props.answer?.kind === 'CHOICE' ? props.answer.option_ids : []))

function choose(optionIds: string[]): void {
  emit('change', optionIds.length ? { v: 1, kind: 'CHOICE', option_ids: optionIds } : null)
}
</script>

<template>
  <UCheckboxGroup
    v-if="question.type === 'MSQ'"
    :model-value="picked"
    :items="items"
    variant="card"
    legend="Choose one or more"
    @update:model-value="value => choose(value as string[])"
  >
    <template #label="{ item }">
      <span class="flex items-start gap-2">
        <span class="font-medium">{{ item.label }}</span>
        <RichContentView :doc="contents.get(String(item.value))" eager-images class="flex-1" />
      </span>
    </template>
  </UCheckboxGroup>
  <URadioGroup
    v-else
    :model-value="picked[0] ?? ''"
    :items="items"
    variant="card"
    @update:model-value="value => choose(value ? [String(value)] : [])"
  >
    <template #label="{ item }">
      <span class="flex items-start gap-2">
        <span class="font-medium">{{ item.label }}</span>
        <RichContentView :doc="contents.get(String(item.value))" eager-images class="flex-1" />
      </span>
    </template>
  </URadioGroup>
</template>
