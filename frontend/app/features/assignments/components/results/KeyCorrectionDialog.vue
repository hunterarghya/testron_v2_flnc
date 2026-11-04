<!-- D-05 Correct the answer key [G-3]: a new correct option (MCQ), options (MSQ) or value and
     tolerance (numerical) for one question, with a required reason. Every ended attempt is
     regraded at once, and published results update; the change is in the audit log. -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { problemMessage } from '~/api/problem-messages'
import type { KeyedPaper, QuestionStat } from '~/api/types'
import { correctAnswerKey } from '~/features/assignments/composables/resultsApi'
import { keyedQuestion } from '~/features/assignments/utils/answer-key'
import RichContentView from '~/shared/components/rich-content/RichContentView.vue'
import { useSubmit } from '~/shared/composables/useSubmit'

const props = defineProps<{ assignmentId: string, stat: QuestionStat | null, keyed: KeyedPaper | null, ended: number }>()
const emit = defineEmits<{ done: [regraded: number] }>()
const open = defineModel<boolean>('open', { required: true })

const picked = ref<string[]>([])
const value = ref('')
const tolerance = ref('0')
const reason = ref('')
const correcting = useSubmit(correctAnswerKey)
const question = computed(() => (props.stat && props.keyed ? keyedQuestion(props.keyed, props.stat.question_id) : null))
const items = computed(() => (question.value?.options ?? []).map(o => ({ value: o.id, label: o.label })))

watch(open, (now) => {
  if (!now || !question.value) return
  picked.value = [...question.value.correct]
  value.value = question.value.answer ?? ''
  tolerance.value = question.value.tolerance ?? '0'
  reason.value = ''
})

async function save(): Promise<void> {
  const q = question.value
  if (!q || !props.stat) return
  const entry = q.type === 'NUMERICAL'
    ? { answer: value.value, tolerance: tolerance.value }
    : { option_ids: picked.value, tolerance: '0' }
  const done = await correcting.submit(props.assignmentId, props.stat.question_id, entry, reason.value)
  if (!done) return
  open.value = false
  emit('done', done.regraded_attempts)
}
</script>

<template>
  <UModal v-model:open="open" :title="`Correct the answer for Q${stat?.number ?? ''}`" :description="`${ended} attempt(s) will be regraded.`">
    <template #body>
      <div v-if="question" class="space-y-4">
        <RichContentView :doc="question.stem" />
        <URadioGroup v-if="question.type === 'MCQ'" :model-value="picked[0]" :items="items" legend="Correct option" @update:model-value="v => picked = [String(v)]" />
        <UCheckboxGroup v-else-if="question.type === 'MSQ'" v-model="picked" :items="items" legend="Correct options" />
        <div v-else class="flex gap-3">
          <UFormField label="Answer">
            <UInput v-model="value" class="w-32 font-mono" />
          </UFormField>
          <UFormField label="± Tolerance">
            <UInput v-model="tolerance" class="w-24 font-mono" />
          </UFormField>
        </div>
        <UFormField label="Reason (kept in the audit log)" required>
          <UTextarea v-model="reason" :rows="2" class="w-full" />
        </UFormField>
        <UAlert v-if="correcting.problem.value" color="error" variant="subtle" :title="problemMessage(correcting.problem.value)" />
      </div>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="outline" @click="open = false" />
        <UButton label="Correct and regrade" :disabled="!reason.trim()" :loading="correcting.pending.value" @click="save" />
      </div>
    </template>
  </UModal>
</template>
