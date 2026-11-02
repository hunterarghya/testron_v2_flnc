<!-- One question in the document (T-03): header, tags, stem, options or answer, solution.
     Every change is saved ~800 ms after the last one, and at once when a field loses focus.
     Keys: Ctrl+Enter new question of this type · Ctrl+D duplicate · Alt+↑/↓ move. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { EditorQuestion, QuestionType, Tag, TestSettings } from '~/api/types'
import NumericAnswer from '~/features/editor/components/NumericAnswer.vue'
import OptionsEditor from '~/features/editor/components/OptionsEditor.vue'
import QuestionHeader from '~/features/editor/components/QuestionHeader.vue'
import { useEditorContext } from '~/features/editor/composables/editorContext'
import { suggestTags } from '~/features/editor/composables/editorApi'
import { focusQuestion } from '~/features/editor/utils/focus'
import type { EditorCommand } from '~/shared/components/rich-content/menus'
import RichField from '~/shared/components/RichField.vue'
import TagPills from '~/shared/components/TagPills.vue'

const props = defineProps<{ number: number, settings: TestSettings, hasProblem: boolean }>()
const question = defineModel<EditorQuestion>('question', { required: true })

const { editor, actions } = useEditorContext()
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
const inserts = computed(() => (props.settings.timing.kind === 'SECTIONED' ? ['question', 'section'] as const : ['question'] as const))

async function addAfter(type: QuestionType): Promise<void> {
  const id = await actions.addQuestion(type, question.value.section_id, question.value.id)
  if (id) focusQuestion(id)
}

function onCommand(command: EditorCommand): void {
  if (command.kind === 'question') void addAfter(command.questionType)
  else void actions.addSection(question.value.section_id)
}

function onKeydown(event: KeyboardEvent): void {
  const mod = event.ctrlKey || event.metaKey
  const id = question.value.id
  let action: (() => unknown) | null = null
  if (mod && event.key === 'Enter') action = () => addAfter(question.value.type)
  else if (mod && event.key.toLowerCase() === 'd') action = () => actions.duplicateQuestion(id)
  else if (event.altKey && event.key === 'ArrowUp') action = () => actions.moveQuestion(id, -1)
  else if (event.altKey && event.key === 'ArrowDown') action = () => actions.moveQuestion(id, 1)
  if (!action || disabled.value) return
  event.preventDefault()
  void action()
}
</script>

<template>
  <section :id="`question-${question.id}`" class="space-y-2 rounded-lg border p-3" :class="hasProblem ? 'border-warning' : 'border-default'" @keydown="onKeydown">
    <QuestionHeader v-model:question="question" :number="number" :settings="settings" :disabled="disabled" @changed="changed" />
    <div class="flex flex-wrap gap-4">
      <TagPills v-model="chapters" label="Chapter" :suggest="typed => suggestTags('CHAPTER', typed)" :disabled="disabled" />
      <TagPills v-model="topics" label="Topic" :suggest="typed => suggestTags('TOPIC', typed)" :disabled="disabled" />
    </div>
    <RichField
      v-model="question.stem"
      placeholder="Type the question… or press / for commands"
      label="Question text"
      :inserts="[...inserts]"
      :disabled="disabled"
      @update:model-value="changed"
      @blur="blurred"
      @command="onCommand"
    />
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
