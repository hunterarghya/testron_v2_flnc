<!-- The test as one document (T-03): title, instructions, then each section's questions. Section
     headers show only in sectioned tests; elsewhere the single section is invisible. -->
<script setup lang="ts">
import { computed } from 'vue'
import type { TestDocument } from '~/api/types'
import AddQuestionMenu from '~/features/editor/components/AddQuestionMenu.vue'
import QuestionBlock from '~/features/editor/components/QuestionBlock.vue'
import SectionHeader from '~/features/editor/components/SectionHeader.vue'
import { useEditorContext } from '~/features/editor/composables/editorContext'
import RichField from '~/shared/components/RichField.vue'

const doc = defineModel<TestDocument>('doc', { required: true })

const { editor } = useEditorContext()
const sectioned = computed(() => doc.value.settings.timing.kind === 'SECTIONED')
const withProblems = computed(() => new Set(doc.value.problems.map(problem => problem.question_id).filter(Boolean)))
// Questions are numbered 1..n across sections, as students see them
const firstNumber = computed(() => {
  let count = 0
  return doc.value.sections.map((section) => {
    const first = count + 1
    count += section.questions.length
    return first
  })
})
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-4">
    <UInput
      v-model="doc.title"
      variant="ghost"
      size="xl"
      class="w-full font-semibold"
      aria-label="Test title"
      :disabled="editor.readOnly.value"
      @update:model-value="editor.edits.test()"
      @blur="editor.flush('test')"
    />
    <RichField
      v-model="doc.instructions"
      placeholder="Instructions for students (optional)"
      label="Instructions"
      :disabled="editor.readOnly.value"
      @update:model-value="editor.edits.test()"
      @blur="editor.flush('test')"
    />
    <template v-for="(section, s) in doc.sections" :key="section.id">
      <SectionHeader v-if="sectioned" v-model:section="doc.sections[s]!" :index="s" :can-delete="doc.sections.length > 1" />
      <QuestionBlock
        v-for="(question, q) in section.questions"
        :key="question.id"
        v-model:question="section.questions[q]!"
        :number="firstNumber[s]! + q"
        :settings="doc.settings"
        :has-problem="withProblems.has(question.id)"
      />
      <UEmpty
        v-if="!section.questions.length && !sectioned"
        icon="i-lucide-file-question"
        title="No questions yet"
        description="Add the first one below."
      />
      <AddQuestionMenu :section-id="section.id" :after-id="section.questions.at(-1)?.id ?? null" :sectioned="sectioned" />
    </template>
  </div>
</template>
