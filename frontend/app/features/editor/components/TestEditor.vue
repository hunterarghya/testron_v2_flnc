<!-- T-03 Test Editor: header with the save state and Preview / Import / Settings, the outline on
     the left (from 1024 px), and the test as one document. Assign arrives with Phase 4. -->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import EditorDocument from '~/features/editor/components/EditorDocument.vue'
import EditorHeader from '~/features/editor/components/EditorHeader.vue'
import EditorOutline from '~/features/editor/components/EditorOutline.vue'
import ImportDialog from '~/features/editor/components/ImportDialog.vue'
import SettingsPanel from '~/features/editor/components/SettingsPanel.vue'
import { provideEditor } from '~/features/editor/composables/editorContext'
import { useEditorActions } from '~/features/editor/composables/useEditorActions'
import { createQuestionDrag, provideQuestionDrag } from '~/features/editor/composables/useQuestionDrag'
import { useTestEditor } from '~/features/editor/composables/useTestEditor'
import ErrorState from '~/shared/components/ErrorState.vue'

const props = defineProps<{ testId: string }>()

const editor = useTestEditor(props.testId)
const actions = useEditorActions(editor, props.testId)
provideEditor({ testId: props.testId, editor, actions })
provideQuestionDrag(createQuestionDrag((questionId, target) => actions.dropQuestion(questionId, target.sectionId, target.beforeId)))
const settingsOpen = ref(false)
const importOpen = ref(false)
const { doc, loadProblem, status } = editor

function reload(): void {
  window.location.reload()
}

onMounted(editor.load)
</script>

<template>
  <ErrorState v-if="loadProblem" :problem="loadProblem" @retry="editor.load" />
  <div v-else-if="doc" class="space-y-4">
    <EditorHeader
      :test-id="testId"
      :title="doc.title"
      :status="status"
      :assigned-before="doc.last_assigned_at !== null"
      @reload="reload"
      @settings="settingsOpen = true"
      @import="importOpen = true"
    />
    <div class="grid gap-6 lg:grid-cols-[14rem_1fr]">
      <aside class="hidden lg:block">
        <div class="sticky top-4">
          <EditorOutline :doc="doc" />
        </div>
      </aside>
      <EditorDocument v-model:doc="doc" />
    </div>
    <SettingsPanel v-model:open="settingsOpen" />
    <ImportDialog v-model:open="importOpen" />
  </div>
  <USkeleton v-else class="h-64 w-full" />
</template>
