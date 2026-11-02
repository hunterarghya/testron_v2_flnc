<!-- T-05 Test Preview: the test as students meet it, stage by stage (one block, each section, or
     each question). Nothing is saved and no clock runs; the exam hall itself arrives in Phase 5
     (ADR-067). "Show answers" adds the key and solutions; "Phone" renders at 390 px. -->
<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { components } from '~/api/schema'
import { getPreview } from '~/features/editor/composables/editorApi'
import PreviewQuestion from '~/features/editor/components/PreviewQuestion.vue'
import ErrorState from '~/shared/components/ErrorState.vue'
import { useApiData } from '~/shared/composables/useApiData'
import RichContentView from '~/shared/components/rich-content/RichContentView.vue'
import { formatDuration } from '~/shared/utils/time'

type Stage = components['schemas']['PreviewStageOut']

const props = defineProps<{ testId: string }>()
const DEVICES = [{ label: 'Laptop', value: 'laptop' }, { label: 'Phone', value: 'phone' }]

const showAnswers = ref(false)
const device = ref('laptop')
const stageIndex = ref(0)
const paper = useApiData(() => getPreview(props.testId, showAnswers.value))
const data = computed(() => paper.data.value)
const stage = computed<Stage | undefined>(() => data.value?.stages[stageIndex.value])
const questions = computed(() => {
  const ids = new Set(stage.value?.question_ids ?? [])
  return (data.value?.questions ?? []).filter(question => ids.has(question.id))
})
const answers = computed(() => new Map((data.value?.answers ?? []).map(answer => [answer.question_id, answer])))
const stageTabs = computed(() => (data.value?.stages ?? []).map(s => ({ value: s.index, label: stageLabel(s) })))

function stageLabel(s: Stage): string {
  const name = s.kind === 'SECTION' ? (s.title || `Section ${s.index + 1}`) : `Question ${s.index + 1}`
  return s.duration_s === null ? name : `${name} · ${formatDuration(s.duration_s)}`
}

watch(showAnswers, () => paper.refresh())
onMounted(paper.refresh)
</script>

<template>
  <ErrorState v-if="paper.error.value" :problem="paper.error.value" @retry="paper.refresh" />
  <div v-else-if="data" class="space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <UButton label="Back to editor" icon="i-lucide-arrow-left" color="neutral" variant="ghost" :to="`/admin/tests/${testId}`" />
      <h1 class="min-w-0 flex-1 truncate text-lg font-semibold">Preview: {{ data.title }}</h1>
      <UBadge label="PREVIEW" color="warning" variant="solid" />
      <USwitch v-model="showAnswers" label="Show answers" />
      <USelect v-model="device" :items="DEVICES" class="w-32" aria-label="Device" />
    </div>
    <p class="text-sm text-muted">Student view. Nothing is saved, the clock doesn't run and integrity checks are off.</p>
    <div class="mx-auto space-y-4" :class="device === 'phone' ? 'max-w-[390px] rounded-xl border border-default p-3' : 'max-w-3xl'">
      <RichContentView v-if="stageIndex === 0" :doc="data.instructions" />
      <UTabs v-if="stageTabs.length > 1" v-model="stageIndex" :items="stageTabs" :content="false" />
      <p v-if="stage?.duration_s" class="text-sm text-muted">Time for this part: {{ formatDuration(stage.duration_s) }}</p>
      <RichContentView :doc="stage?.instructions" />
      <PreviewQuestion v-for="question in questions" :key="question.id" :question="question" :answer="answers.get(question.id)" />
      <UEmpty v-if="!questions.length" icon="i-lucide-file-question" title="No questions here yet." />
    </div>
  </div>
  <USkeleton v-else class="h-64 w-full" />
</template>
