<!-- One question in the document (T-03): header, tags, stem, options or answer, solution.
     Every change is saved ~800 ms after the last one, and at once when a field loses focus. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { EditorQuestion, Tag, TestSettings } from '~/api/types'
import NumericAnswer from '~/features/editor/components/NumericAnswer.vue'
import OptionsEditor from '~/features/editor/components/OptionsEditor.vue'
import QuestionHeader from '~/features/editor/components/QuestionHeader.vue'
import { useEditorContext } from '~/features/editor/composables/editorContext'
import { suggestTags } from '~/features/editor/composables/editorApi'
import RichField from '~/shared/components/RichField.vue'
import TagPills from '~/shared/components/TagPills.vue'

defineProps<{ number: number, settings: TestSettings, hasProblem: boolean }>()
const question = defineModel<EditorQuestion>('question', { required: true })

const { editor } = useEditorContext()
const showSolution = ref(question.value.solution !== null)
const disabled = computed(() => editor.readOnly.value)

const changed = () => editor.edits.question(question.value)
const blurred = () => editor.flush(`question:${question.value.id}`)

function tagNames(kind: 'chapter_tags' | 'topic_tags') {
  return computed({
    get: () => question.value[kind].map(tag => tag.name),
    set: (names: string[]) => {
      const known = new Map(question.value[kind].map(tag => [tag.name, tag]))
      const tagKind = kind === 'chapter_tags' ? 'CHAPTER' : 'TOPIC'
      // New names have no id until saved; the server creates the tag (domain_model.md §4.1)
      question.value[kind] = names.map((name): Tag => known.get(name) ?? { id: '', kind: tagKind, name })
      changed()
    },
  })
}
const chapters = tagNames('chapter_tags')
const topics = tagNames('topic_tags')
</script>

<template>
  <section :id="`question-${question.id}`" class="space-y-2 rounded-lg border p-3" :class="hasProblem ? 'border-warning' : 'border-default'">
    <QuestionHeader v-model:question="question" :number="number" :settings="settings" :disabled="disabled" @changed="changed" />
    <div class="flex flex-wrap gap-4">
      <TagPills v-model="chapters" label="Chapter" :suggest="typed => suggestTags('CHAPTER', typed)" :disabled="disabled" />
      <TagPills v-model="topics" label="Topic" :suggest="typed => suggestTags('TOPIC', typed)" :disabled="disabled" />
    </div>
    <RichField v-model="question.stem" placeholder="Type the question…" label="Question text" :disabled="disabled" @update:model-value="changed" @blur="blurred" />
    <NumericAnswer v-if="question.type === 'NUMERICAL'" v-model:question="question" :disabled="disabled" @changed="changed" @blur="blurred" />
    <OptionsEditor v-else v-model:question="question" :disabled="disabled" @changed="changed" @blur="blurred" />
    <UButton
      v-if="!showSolution"
      label="Solution (optional)"
      icon="i-lucide-chevron-right"
      color="neutral"
      variant="ghost"
      size="xs"
      @click="showSolution = true"
    />
    <RichField
      v-else
      v-model="question.solution"
      placeholder="Explain the answer (shown to students only if you publish solutions)"
      label="Solution"
      :disabled="disabled"
      @update:model-value="changed"
      @blur="blurred"
    />
  </section>
</template>
