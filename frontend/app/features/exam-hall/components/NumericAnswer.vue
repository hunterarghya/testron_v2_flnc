<!-- A numerical question's answer box (P-03): the keypad is always beside it, and the physical
     keyboard goes through the same rules. On touch screens the device keyboard stays hidden
     (inputmode="none") so the question stays in view. Only a complete number is saved; the
     box empty is a cleared answer. The hall keys it by question, so each starts from its saved value. -->
<script setup lang="ts">
import { nextTick, ref } from 'vue'
import type { HallAnswer } from '~/api/types'
import { applyNumericText, isCompleteNumber } from '~/engine/keyboards'
import NumericKeypad from '~/features/exam-hall/components/NumericKeypad.vue'

const props = defineProps<{ answer: HallAnswer | null }>()
const emit = defineEmits<{ change: [answer: HallAnswer | null] }>()

const text = ref(savedValue())

function savedValue(): string {
  return props.answer?.kind === 'NUMERIC' ? props.answer.value : ''
}

async function typed(raw: string | number): Promise<void> {
  const value = applyNumericText('', String(raw))
  // Let the box take the raw text first, so a refused key is removed from view too
  text.value = String(raw)
  await nextTick()
  text.value = value
  if (value === '') emit('change', null)
  else if (isCompleteNumber(value)) emit('change', { v: 1, kind: 'NUMERIC', value })
}
</script>

<template>
  <div class="space-y-3">
    <UFormField label="Your answer">
      <UInput
        :model-value="text"
        inputmode="none"
        autocomplete="off"
        size="xl"
        class="w-full max-w-xs font-mono"
        @update:model-value="typed"
      />
    </UFormField>
    <NumericKeypad :value="text" @input="typed" />
  </div>
</template>
