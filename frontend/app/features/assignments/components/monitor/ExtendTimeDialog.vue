<!-- D-03 Extend time: + N minutes for everyone or the selected students. In a sectioned test,
     the current section or the final one. Shows when the test ends now. Students see it on
     their next save or heartbeat (about 15 s). -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { problemMessage } from '~/api/problem-messages'
import { extendTime } from '~/features/assignments/composables/monitorApi'
import { useSubmit } from '~/shared/composables/useSubmit'
import { formatTime } from '~/shared/utils/time'

const props = defineProps<{
  assignmentId: string
  // Empty: everyone
  studentIds: string[]
  sectioned: boolean
  // The section most students are in now (sectioned tests)
  currentStage: number | null
}>()
const emit = defineEmits<{ done: [] }>()
const open = defineModel<boolean>('open', { required: true })

const minutes = ref(10)
const section = ref<'final' | 'current'>('final')
const extending = useSubmit(extendTime)
const endsAt = ref<string | null>(null)
const who = computed(() => (props.studentIds.length ? `${props.studentIds.length} selected student${props.studentIds.length === 1 ? '' : 's'}` : 'everyone'))
const sections = computed(() => [
  { value: 'final', label: 'Final section' },
  ...(props.currentStage === null ? [] : [{ value: 'current', label: `Current section (S${props.currentStage + 1})` }]),
])

watch(open, (now) => {
  if (now) endsAt.value = null
})

async function extend(): Promise<void> {
  const result = await extending.submit(props.assignmentId, {
    seconds: Math.round(minutes.value * 60),
    ...(props.studentIds.length ? { student_ids: props.studentIds } : {}),
    ...(section.value === 'current' && props.currentStage !== null ? { stage_index: props.currentStage } : {}),
  })
  if (!result) return
  endsAt.value = result.ends_at ?? null
  emit('done')
}
</script>

<template>
  <UModal v-model:open="open" title="Extend time" :description="`Extra time for ${who}.`">
    <template #body>
      <div class="space-y-4">
        <UFormField label="Extra minutes">
          <UInputNumber v-model="minutes" :min="1" :max="1440" class="w-32" />
        </UFormField>
        <UFormField v-if="sectioned" label="Add it to">
          <URadioGroup v-model="section" :items="sections" />
        </UFormField>
        <UAlert v-if="extending.problem.value" color="error" variant="subtle" :title="problemMessage(extending.problem.value)" />
        <UAlert
          v-if="endsAt"
          color="success"
          variant="subtle"
          :title="`Done. The test now ends at ${formatTime(endsAt)}.`"
        />
      </div>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Close" color="neutral" variant="outline" @click="open = false" />
        <UButton :label="`Add ${minutes} min`" :loading="extending.pending.value" @click="extend" />
      </div>
    </template>
  </UModal>
</template>
