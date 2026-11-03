<!-- The numeric keypad beside a numerical question (screens.md §4.0). What each key does is
     engine/keyboards.ts; this only draws the keys. -->
<script setup lang="ts">
import { applyNumericKey, NUMERIC_KEYS, type NumericKey } from '~/engine/keyboards'

const props = defineProps<{ value: string, disabled?: boolean }>()
const emit = defineEmits<{ input: [value: string] }>()

function press(key: NumericKey): void {
  emit('input', applyNumericKey(props.value, key))
}

function label(key: NumericKey): string {
  return key === '-' ? '−' : key
}
</script>

<template>
  <div class="flex gap-2" role="group" aria-label="Number keypad">
    <div class="grid grid-cols-3 gap-2">
      <UButton
        v-for="key in NUMERIC_KEYS"
        :key="key"
        :label="label(key)"
        :aria-label="key === '-' ? 'Minus' : key === '.' ? 'Point' : key"
        color="neutral"
        variant="outline"
        size="lg"
        class="justify-center font-mono"
        :disabled="disabled"
        @click="press(key)"
      />
    </div>
    <div class="flex flex-col gap-2">
      <UButton icon="i-lucide-delete" aria-label="Delete" color="neutral" variant="outline" size="lg" :disabled="disabled" @click="press('backspace')" />
      <UButton label="Clear" color="neutral" variant="outline" size="lg" :disabled="disabled" @click="press('clear')" />
    </div>
  </div>
</template>
