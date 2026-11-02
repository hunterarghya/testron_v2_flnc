<!-- One rich-content field (stem, option, solution, instructions). Interim version: plain text,
     one paragraph per line (ADR-065). Step 3.8 replaces the inside with TipTap; the props and
     events stay the same. Content with formatting is shown, not flattened. -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { RichDoc } from '~/api/types'
import { docToText, isPlainDoc, summaryText, textToDoc } from '~/shared/utils/plain-doc'

defineProps<{
  placeholder?: string
  // full: stem, solution, instructions · compact: an option (editor_content_spec.md §1)
  profile?: 'full' | 'compact'
  disabled?: boolean
  label?: string
}>()
const model = defineModel<RichDoc | null>({ required: true })
const emit = defineEmits<{ blur: [] }>()

const text = ref(docToText(model.value))
const editable = computed(() => isPlainDoc(model.value))

watch(model, (doc) => {
  // Outside changes (a reload, an import) replace the text; our own echo doesn't
  if (docToText(doc) !== text.value) text.value = docToText(doc)
})

function onInput(value: string | number): void {
  text.value = String(value)
  model.value = textToDoc(text.value)
}
</script>

<template>
  <UTextarea
    v-if="editable"
    :model-value="text"
    :placeholder="placeholder"
    :rows="profile === 'compact' ? 1 : 2"
    :disabled="disabled"
    :aria-label="label ?? placeholder"
    autoresize
    variant="ghost"
    class="w-full"
    @update:model-value="onInput"
    @blur="emit('blur')"
  />
  <p v-else class="rounded-md bg-elevated px-3 py-2 text-sm" :aria-label="label">
    {{ summaryText(model) }}
    <span class="block text-xs text-muted">Formatted content: editable with the rich editor.</span>
  </p>
</template>
