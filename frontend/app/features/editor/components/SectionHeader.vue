<!-- A section's header in a sectioned test (T-03): its name and duration (minutes), and ⋯ Delete.
     A section with questions asks whether to move them to the previous section or delete them. -->
<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import { computed, ref } from 'vue'
import type { EditorSection } from '~/api/types'
import { useEditorContext } from '~/features/editor/composables/editorContext'

const props = defineProps<{ index: number, canDelete: boolean }>()
const section = defineModel<EditorSection>('section', { required: true })

const { editor, actions } = useEditorContext()
const deleting = ref(false)
const disabled = computed(() => editor.readOnly.value)
const minutes = computed({
  get: () => (section.value.duration_s === null ? null : Math.round(section.value.duration_s / 60)),
  set: (value: number | null) => {
    section.value.duration_s = value === null ? null : value * 60
    editor.edits.section(section.value)
  },
})
const menu = computed<DropdownMenuItem[]>(() => [
  { label: 'Add a section after this', icon: 'i-lucide-plus', onSelect: () => actions.addSection(section.value.id) },
  { label: 'Delete section', icon: 'i-lucide-trash-2', color: 'error', disabled: !props.canDelete, onSelect: () => onDelete() },
])

function onDelete(): void {
  if (section.value.questions.length) deleting.value = true
  else void actions.deleteSection(section.value.id, null)
}

async function remove(questions: 'move_to_previous' | 'delete'): Promise<void> {
  deleting.value = false
  await actions.deleteSection(section.value.id, questions)
}
</script>

<template>
  <div :id="`section-${section.id}`" class="flex flex-wrap items-center gap-3 border-b-2 border-default pb-2 pt-4">
    <span class="text-sm font-semibold text-muted">Section {{ index + 1 }}</span>
    <UInput
      v-model="section.title"
      placeholder="Section name"
      variant="ghost"
      class="flex-1 font-semibold"
      :disabled="disabled"
      aria-label="Section name"
      @update:model-value="editor.edits.section(section)"
      @blur="editor.flush(`section:${section.id}`)"
    />
    <UFormField label="Minutes" orientation="horizontal">
      <UInputNumber v-model="minutes" :min="1" :max="1440" class="w-28" :disabled="disabled" />
    </UFormField>
    <UDropdownMenu :items="menu" :disabled="disabled">
      <UButton icon="i-lucide-ellipsis" color="neutral" variant="ghost" size="xs" :aria-label="`More for section ${index + 1}`" />
    </UDropdownMenu>
    <UModal v-model:open="deleting" :title="`Delete section ${index + 1}?`" :description="`It has ${section.questions.length} question(s). Move them to the previous section, or delete them too?`">
      <template #footer>
        <div class="flex w-full justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" @click="deleting = false" />
          <UButton label="Move questions" color="neutral" variant="outline" @click="remove('move_to_previous')" />
          <UButton label="Delete them too" color="error" @click="remove('delete')" />
        </div>
      </template>
    </UModal>
  </div>
</template>
