<!-- One rich-content field (stem, option, solution, instructions). The TipTap editor is loaded on
     first use, so only the teacher's editor pages download it (frontend_spec.md §1). -->
<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import type { RichDoc } from '~/api/types'
import type { EditorCommand, PageInsert } from '~/shared/components/rich-content/menus'

withDefaults(defineProps<{
  placeholder?: string
  // full: stem, solution, instructions · compact: an option (editor_content_spec.md §1)
  profile?: 'full' | 'compact'
  disabled?: boolean
  label?: string
  // Question or section inserts in the "/" menu (a stem only)
  inserts?: PageInsert[]
  captureEnter?: boolean
  captureEmptyBackspace?: boolean
}>(), { profile: 'full', placeholder: undefined, label: undefined, inserts: () => [] })
const model = defineModel<RichDoc | null>({ required: true })
const emit = defineEmits<{ blur: [], command: [command: EditorCommand], enter: [], emptyBackspace: [] }>()

const RichContentEditor = defineAsyncComponent(() => import('~/shared/components/rich-content/RichContentEditor.vue'))
</script>

<template>
  <RichContentEditor
    v-model="model"
    :profile="profile"
    :placeholder="placeholder"
    :disabled="disabled"
    :label="label"
    :inserts="inserts"
    :capture-enter="captureEnter"
    :capture-empty-backspace="captureEmptyBackspace"
    @blur="emit('blur')"
    @enter="emit('enter')"
    @empty-backspace="emit('emptyBackspace')"
    @command="(command: EditorCommand) => emit('command', command)"
  />
</template>
