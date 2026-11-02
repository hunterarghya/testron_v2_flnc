<!-- The on-screen QWERTY keyboard (screens.md §4.0), docked at the bottom of the page.
     It types into the bound text; the physical keyboard keeps working alongside it.
     Done, Esc or a click outside closes it. What each key does is engine/keyboards.ts. -->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  DIGIT_ROW,
  initialKeyboardState,
  type KeyPress,
  LETTER_ROWS,
  pressKey,
  SYMBOL_ROWS,
} from '~/engine/keyboards'

const value = defineModel<string>({ required: true })
const open = defineModel<boolean>('open', { required: true })

const state = ref(initialKeyboardState())
const panel = ref<HTMLElement | null>(null)
const rows = computed(() => (state.value.layer === 'letters' ? LETTER_ROWS : SYMBOL_ROWS))

function press(key: KeyPress): void {
  state.value = pressKey({ ...state.value, value: value.value }, key)
  value.value = state.value.value
}

function label(char: string): string {
  return state.value.shift ? char.toUpperCase() : char
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    open.value = false
  }
}

function onPointerDown(event: PointerEvent): void {
  const target = event.target as Node | null
  // The ⌨ buttons toggle the keyboard themselves
  const toggle = target instanceof Element && target.closest('[data-keyboard-toggle]')
  if (panel.value && target && !panel.value.contains(target) && !toggle) {
    open.value = false
  }
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('pointerdown', onPointerDown)
})
onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('pointerdown', onPointerDown)
})
</script>

<template>
  <div
    v-if="open"
    ref="panel"
    class="fixed inset-x-0 bottom-0 z-50 border-t border-default bg-elevated p-2 shadow-lg"
    role="group"
    aria-label="On-screen keyboard"
  >
    <div class="mx-auto flex max-w-3xl flex-col gap-1">
      <div class="flex flex-wrap justify-center gap-1">
        <UButton v-for="char in DIGIT_ROW" :key="char" :label="char" color="neutral" variant="outline" @click="press({ kind: 'char', char })" />
        <UButton icon="i-lucide-delete" aria-label="Backspace" color="neutral" variant="outline" @click="press({ kind: 'backspace' })" />
      </div>
      <div v-for="(row, index) in rows" :key="index" class="flex flex-wrap justify-center gap-1">
        <UButton v-if="index === rows.length - 1" icon="i-lucide-arrow-big-up" aria-label="Shift" :variant="state.shift ? 'solid' : 'outline'" color="neutral" @click="press({ kind: 'shift' })" />
        <UButton v-for="char in row" :key="char" :label="label(char)" color="neutral" variant="outline" @click="press({ kind: 'char', char })" />
        <template v-if="index === rows.length - 1">
          <UButton :label="state.layer === 'letters' ? '!#$' : 'abc'" color="neutral" variant="outline" @click="press({ kind: 'layer' })" />
          <UButton label="Done" @click="open = false" />
        </template>
      </div>
    </div>
  </div>
</template>
