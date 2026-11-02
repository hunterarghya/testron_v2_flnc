<!-- Chapter or topic tags on a question (T-03, [C-8]): type to see matching tags already used
     anywhere; Enter picks one, or creates the typed name. ✕ removes a tag from this question
     only. Names are compared ignoring case and spaces, so "cell" and "Cell " are one tag. -->
<script setup lang="ts">
import { onScopeDispose, ref, watch } from 'vue'

const props = defineProps<{
  label: string
  suggest: (typed: string) => Promise<string[]>
  disabled?: boolean
}>()
const names = defineModel<string[]>({ required: true })

const SUGGEST_DELAY_MS = 200
const term = ref('')
const items = ref<string[]>([])

const same = (a: string, b: string) => tidy(a).toLocaleLowerCase() === tidy(b).toLocaleLowerCase()

function tidy(name: string): string {
  return name.trim().replace(/\s+/g, ' ')
}

function onCreate(typed: string): void {
  const name = tidy(typed)
  if (name && !names.value.some(existing => same(existing, name))) {
    names.value = [...names.value, name]
  }
  term.value = ''
}

let timer: ReturnType<typeof setTimeout> | undefined
watch(term, (typed) => {
  clearTimeout(timer)
  timer = setTimeout(async () => {
    // A failed lookup only means no suggestions; typing a new tag still works
    items.value = await props.suggest(typed).catch(() => [])
  }, SUGGEST_DELAY_MS)
})
onScopeDispose(() => clearTimeout(timer))
</script>

<template>
  <div class="flex items-center gap-2">
    <span class="text-xs text-muted">{{ label }}</span>
    <UInputMenu
      v-model="names"
      v-model:search-term="term"
      :items="items"
      multiple
      create-item
      ignore-filter
      :disabled="disabled"
      :aria-label="label"
      placeholder="+"
      size="xs"
      variant="ghost"
      class="min-w-24"
      @create="onCreate"
    />
  </div>
</template>
