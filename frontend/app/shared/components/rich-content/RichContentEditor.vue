<!-- One rich field, editable (editor_content_spec.md §4): Nuxt UI's editor with our schema, a
     format bar on selection, "/" for inserts, pasting cleaned on the way in, images uploaded.
     The stored format comes in and goes out; the editor's own format stays inside. -->
<script setup lang="ts">
import type { Editor, JSONContent } from '@tiptap/core'
import 'katex/dist/katex.min.css'
import { computed, ref, shallowRef, watch } from 'vue'
import { useToast } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import type { RichDoc } from '~/api/types'
import { fromEditor, type PmNode, toEditor } from '~/shared/components/rich-content/convert'
import { type Profile, richExtensions, starterKitOptions } from '~/shared/components/rich-content/extensions'
import { usePaste } from '~/shared/components/rich-content/usePaste'
import { type EditorCommand, type PageInsert, slashItems, toolbarItems, useInsertHandlers } from '~/shared/components/rich-content/menus'

const props = defineProps<{
  profile: Profile
  placeholder?: string
  disabled?: boolean
  label?: string
  inserts?: PageInsert[]
}>()
const model = defineModel<RichDoc | null>({ required: true })
const emit = defineEmits<{ blur: [], command: [command: EditorCommand] }>()

const toast = useToast()
const notify = (problem: Parameters<typeof problemMessage>[0]) => toast.add({ title: problemMessage(problem), color: 'error' })
const picker = ref<HTMLInputElement | null>(null)
// Nuxt UI's editor component exposes the TipTap editor it made
const root = shallowRef<{ editor?: Editor } | null>(null)
const editorRef = computed(() => root.value?.editor ?? null)
const extensions = richExtensions(props.profile)
const content = ref<JSONContent>(toEditor(model.value) as JSONContent)
const paste = usePaste(() => editorRef.value, notify)
const handlers = useInsertHandlers({ pickImage: () => picker.value?.click(), command: command => emit('command', command) })
const slash = computed(() => slashItems(props.profile, props.inserts))
const toolbar = computed(() => toolbarItems(props.profile))

function onUpdate(json: JSONContent): void {
  content.value = json
  model.value = fromEditor(json as PmNode)
}

// A reload or an outside change replaces the content; our own echo doesn't
watch(model, (doc) => {
  if (JSON.stringify(doc) !== JSON.stringify(fromEditor(content.value as PmNode))) {
    content.value = toEditor(doc) as JSONContent
  }
})
watch(() => props.disabled, disabled => editorRef.value?.setEditable(!disabled))

function onPicked(event: Event): void {
  const input = event.target as HTMLInputElement
  const files = [...(input.files ?? [])]
  input.value = ''
  if (editorRef.value) paste.uploadFiles(editorRef.value, files)
}
</script>

<template>
  <UEditor
    ref="root"
    v-slot="{ editor }"
    :model-value="content"
    content-type="json"
    :starter-kit="starterKitOptions(profile)"
    :extensions="extensions"
    :image="false"
    :mention="false"
    :placeholder="placeholder"
    :editable="!disabled"
    :handlers="handlers"
    :editor-props="paste.editorProps"
    :aria-label="label ?? placeholder"
    class="w-full"
    :ui="{ base: profile === 'compact' ? 'min-h-6' : 'min-h-12' }"
    @update:model-value="onUpdate"
    @blur="emit('blur')"
  >
    <UEditorToolbar :editor="editor" :items="toolbar" layout="bubble" />
    <UEditorSuggestionMenu :editor="editor" :items="slash" />
    <input ref="picker" type="file" accept="image/png,image/jpeg,image/webp,image/gif" multiple class="hidden" @change="onPicked">
  </UEditor>
</template>
